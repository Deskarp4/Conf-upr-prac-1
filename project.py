import tkinter as tk
import argparse
import os
import sys
import csv
import base64

class VFSNode:
    def __init__(self, name, is_dir):
        self.name = name
        self.is_dir = is_dir
        self.children = {}
        self.content = b""
        self.owner = None

    def add_child(self, node):
        self.children[node.name] = node

    def get_child(self, name):
        return self.children.get(name)

    def list_children(self):
        return sorted([(n, self.children[n].is_dir) for n in self.children])

class VFS:
    def __init__(self):
        self.root = VFSNode("", True)

    def _parts(self, path):
        p = path.strip()
        if p.startswith("/"):
            p = p[1:]
        if not p:
            return []
        return [x for x in p.split("/") if x]

    def mkdirs(self, parts):
        cur = self.root
        for part in parts:
            child = cur.get_child(part)
            if child is None:
                child = VFSNode(part, True)
                cur.add_child(child)
            elif not child.is_dir:
                raise ValueError(f"Path component '{part}' exists as file")
            cur = child
        return cur

    def add_dir(self, path):
        parts = self._parts(path)
        self.mkdirs(parts)

    def add_file(self, path, content_bytes=b""):
        parts = self._parts(path)
        if not parts:
            raise ValueError("File must have a name")
        parent = self.mkdirs(parts[:-1])
        fname = parts[-1]
        if fname in parent.children and parent.children[fname].is_dir:
            raise ValueError(f"Cannot create file: '{fname}' is an existing directory")
        node = VFSNode(fname, False)
        node.content = content_bytes
        parent.children[fname] = node

    def resolve(self, cwd_parts, target):
        if target.startswith("/"):
            parts = self._parts(target)
            cur = self.root
            base = []
        else:
            parts = self._parts(target)
            cur = self.root
            base = list(cwd_parts)
            for p in base:
                cur = cur.get_child(p)
                if cur is None or not cur.is_dir:
                    return None, None

        for part in parts:
            if part == ".":
                continue
            if part == "..":
                if base:
                    base.pop()
                    cur = self.root
                    for p in base:
                        cur = cur.get_child(p)
                else:
                    cur = self.root
                continue
            child = cur.get_child(part)
            if child is None:
                return None, None
            cur = child
            base.append(part)
        return cur, base


class VFS_REPL_App:
    def __init__(self, root, vfs_path=None, script_path=None):
        self.root = root
        self.root.title("VFS Emulator (stage3)")

  
        self.vfs_csv_path = vfs_path
        self.script_path = script_path


        self.cwd_parts = []
        self.vfs = VFS()


        self.create_widgets()


        self.print_output("=== ПАРАМЕТРЫ ЗАПУСКА ===")
        self.print_output(f"vfs_path: {self.vfs_csv_path or '(не указан)'}")
        self.print_output(f"script  : {self.script_path or '(не указан)'}")
        self.print_output("==========================\n")


        if self.vfs_csv_path:
            self.load_vfs(self.vfs_csv_path)


        self.show_motd()


        if self.script_path:
            self.run_script(self.script_path)

        self.input_field.focus_set()


    def create_widgets(self):
        self.output = tk.Text(self.root, height=22, width=100, state=tk.NORMAL)
        self.output.pack(fill="both", expand=True, padx=6, pady=6)

        self.cwd_label = tk.Label(self.root, text=self._cwd_text(), anchor="w")
        self.cwd_label.pack(fill="x", padx=6)

        self.input_field = tk.Entry(self.root, width=80)
        self.input_field.pack(fill="x", padx=6, pady=(4,6))
        self.input_field.bind("<Return>", self.on_enter)

    def _cwd_text(self):
        return "Рабочая директория: /" + ("/".join(self.cwd_parts) if self.cwd_parts else "")

    def update_cwd_label(self):
        self.cwd_label.config(text=self._cwd_text())

    def print_output(self, text=""):
        self.output.insert(tk.END, text + "\n")
        self.output.see(tk.END)


    def load_vfs(self, csv_path):
        self.print_output(f"Загрузка VFS из CSV: {csv_path}")
        if not os.path.isfile(csv_path):
            msg = f"Ошибка: CSV-файл VFS не найден: {csv_path}"
            self.print_output(msg)
            print(msg, file=sys.stderr)
            return False
        try:
            with open(csv_path, newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                if 'path' not in reader.fieldnames or 'type' not in reader.fieldnames:
                    raise ValueError("CSV должен содержать заголовки: path,type[,content_base64]")
                self.vfs = VFS()
                for row in reader:
                    p = (row.get('path') or "").strip()
                    t = (row.get('type') or "").strip().lower()
                    cb64 = (row.get('content_base64') or "")
                    if not p:
                        raise ValueError("Пустое значение path в CSV")
                    if t == 'dir':
                        self.vfs.add_dir(p)
                    elif t == 'file':
                        try:
                            b = base64.b64decode(cb64) if cb64 else b""
                        except Exception as ex:
                            raise ValueError(f"Base64 decode error for path '{p}': {ex}")
                        self.vfs.add_file(p, b)
                    else:
                        raise ValueError(f"Неверный type '{t}' для path '{p}'")
            self.print_output("VFS успешно загружен в память.")
            return True
        except Exception as e:
            msg = f"Ошибка загрузки VFS: {e}"
            self.print_output(msg)
            print(msg, file=sys.stderr)
            return False

    def show_motd(self):
        node, _ = self.vfs.resolve([], "motd")
        if node and not node.is_dir:
            try:
                text = node.content.decode('utf-8', errors='replace')
                self.print_output("----- motd -----")
                for line in text.splitlines():
                    self.print_output(line)
                self.print_output("----------------")
            except Exception as e:
                self.print_output(f"motd есть, но ошибка чтения: {e}")


    def on_enter(self, event=None):
        line = self.input_field.get().strip()
        self.input_field.delete(0, tk.END)
        if not line:
            return
        self.print_output(f"$ {line}")
        try:
            ok = self.handle_line(line)
            if ok is False:
                self.print_output("Ошибка выполнения команды.")
        except SystemExit:
            self.print_output("Завершение приложения.")
            self.root.after(50, self.root.quit)
        except Exception as e:
            self.print_output(f"Внутренняя ошибка: {e}")

    def handle_line(self, line):
        parts = line.strip().split()
        if not parts:
            return True
        cmd = parts[0]
        args = parts[1:]

        if cmd == "ls":
            return self.cmd_ls(args)
        if cmd == "cd":
            return self.cmd_cd(args)

        if cmd == "exit":
            return self.cmd_exit(args)

        self.print_output(f"Неизвестная команда: {cmd}")
        return False


    def cmd_ls(self, args):
        path = args[0] if args else "."
        node, _ = self.vfs.resolve(self.cwd_parts, path)
        if node is None:
            self.print_output(f"ls: путь не найден: {path}")
            return False
        if not node.is_dir:
            self.print_output(f"ls: {path} — не директория")
            return False
        for name, is_dir in node.list_children():
            self.print_output(f"{name}\t{'<dir>' if is_dir else '<file>'}")
        return True


    def cmd_cd(self, args):
        if len(args) > 1:
            self.print_output("cd: слишком много аргументов")
            return False
        target = args[0] if args else "/"
        node, parts = self.vfs.resolve(self.cwd_parts, target)
        if node is None:
            self.print_output(f"cd: путь не найден: {target}")
            return False
        if not node.is_dir:
            self.print_output(f"cd: не директория: {target}")
            return False
        self.cwd_parts = parts
        self.update_cwd_label()
        return True

    def cmd_exit(self, args):
        if args:
            self.print_output("exit: не принимает аргументов")
            return False
        raise SystemExit()


    def run_script(self, path):
        self.print_output(f"\n=== ВЫПОЛНЕНИЕ СКРИПТА {path} ===")
        if not os.path.exists(path):
            self.print_output(f"Ошибка: файл скрипта '{path}' не найден.")
            return
        try:
            with open(path, "r", encoding='utf-8') as f:
                self.script_lines = [
                    line.rstrip("\n") for line in f
                    if line.strip() and not line.strip().startswith("#")
                ]
            self.script_index = 0
            self.root.after(100, self.run_next_script_line)
        except Exception as e:
            self.print_output(f"Ошибка открытия скрипта: {e}")

    def run_next_script_line(self):
        if self.script_index >= len(self.script_lines):
            self.print_output("=== Скрипт завершен ===")
            return
        line = self.script_lines[self.script_index]
        self.script_index += 1
        self.print_output(f"> {line}")
        ok = self.handle_line(line)
        if ok is False:
            self.print_output(f"Стартовый скрипт: ошибка на строке {self.script_index}: '{line}'. Выполнение прервано.")
            return
        self.root.after(120, self.run_next_script_line)


def parse_args():
    p = argparse.ArgumentParser(description="VFS Shell Emulator (stage3)")
    p.add_argument("--vfs-path", dest="vfs_path", help="CSV describing VFS (path,type,content_base64)")
    p.add_argument("--script", dest="script", help="Startup script to run")
    return p.parse_args()

def main():
    args = parse_args()
    print("Запуск VFS-эмулятора (stage3). Параметры:")
    print("  vfs_path:", args.vfs_path)
    print("  script  :", args.script)

    root = tk.Tk()
    app = VFS_REPL_App(root, vfs_path=args.vfs_path, script_path=args.script)
    root.mainloop()

if __name__ == "__main__":
    main()
