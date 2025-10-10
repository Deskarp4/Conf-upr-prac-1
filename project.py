import tkinter as tk
import argparse
import os

class VFS_REPL_App:
    def __init__(self, root, vfs_path=None, script_path=None):
        self.root = root
        self.root.title("VFS Emulator (stage3)")
        self.vfs_csv_path = vfs_path
        self.script_path = script_path
        self.cwd_parts = []
        self.create_widgets()
        self.print_output("=== ПАРАМЕТРЫ ЗАПУСКА ===")
        self.print_output(f"vfs_path: {self.vfs_csv_path or '(не указан)'}")
        self.print_output(f"script  : {self.script_path or '(не указан)'}")
        self.print_output("==========================\n")
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
            self.print_output(f"[LS] Аргументы: {args}")
            return True
        if cmd == "cd":
            self.print_output(f"[CD] Аргументы: {args}")
            return True
        if cmd == "exit":
            if args:
                self.print_output("exit: не принимает аргументов")
                return False
            raise SystemExit()
        self.print_output(f"Неизвестная команда: {cmd}")
        return False

    def run_script(self, path):
        self.print_output(f"\n=== ВЫПОЛНЕНИЕ СКРИПТА {path} ===")
        if not os.path.exists(path):
            self.print_output(f"Ошибка: файл скрипта '{path}' не найден.")
            return
        try:
            with open(path, "r", encoding='utf-8') as f:
                self.script_lines = [line.rstrip("\n") for line in f if line.strip() and not line.strip().startswith("#")]
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
