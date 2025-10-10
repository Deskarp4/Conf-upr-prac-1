import tkinter as tk

class VFS_REPL_App:
    def __init__(self, root):
        self.root = root
        self.root.title("VFS")
        self.cwd = "/"
        self.create_widgets()

    def create_widgets(self):
        self.output = tk.Text(self.root, height=20, width=70)
        self.output.pack(padx=10, pady=10)
        self.cwd_label = tk.Label(self.root, text=self._cwd_text(), anchor="w")
        self.cwd_label.pack(fill="x", padx=10, pady=(0,5))
        self.input_field = tk.Entry(self.root, width=70)
        self.input_field.pack(padx=10, pady=(0,10))
        self.input_field.bind("<Return>", self.on_enter)
        self.input_field.focus_set()

    def _cwd_text(self):
        return f"Рабочая директория: {self.cwd}"

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
        self.handle_line(line)

    def handle_line(self, line):
        parts = line.split()
        if not parts:
            return
        cmd = parts[0]
        args = parts[1:]
        if cmd == "ls":
            self.print_output(f"[LS] Аргументы: {args}")
        elif cmd == "cd":
            if len(args) > 1:
                self.print_output("cd: слишком много аргументов")
            else:
                self.print_output(f"[CD] Аргументы: {args}")
        elif cmd == "exit":
            if args:
                self.print_output("exit: не принимает аргументов")
            else:
                self.root.quit()
        else:
            self.print_output(f"Ошибка: неизвестная команда '{cmd}'")

def main():
    root = tk.Tk()
    app = VFS_REPL_App(root)
    root.mainloop()

if __name__ == "__main__":
    main()
