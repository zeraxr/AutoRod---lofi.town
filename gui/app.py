import tkinter as tk
from tkinter import ttk
from core.bot import AutoFisherBot


class AutoRodGUI:
    """Maneja la interfaz gráfica de usuario."""

    def __init__(self, root):
        self.root = root
        self.root.title("AutoRod Pro")
        self.root.geometry("300x150")
        self.root.resizable(False, False)

        self.bot = AutoFisherBot()
        self._build_ui()

    def _build_ui(self):
        ttk.Label(self.root, text="AutoRod Pro", font=("Helvetica", 16, "bold")).pack(pady=10)
        self.status_label = ttk.Label(self.root, text="Estado: Detenido", foreground="red")
        self.status_label.pack(pady=5)

        button_frame = ttk.Frame(self.root)
        button_frame.pack(pady=10)

        self.start_btn = ttk.Button(button_frame, text="Iniciar", command=self.start_bot)
        self.start_btn.grid(row=0, column=0, padx=5)

        self.stop_btn = ttk.Button(button_frame, text="Detener", command=self.stop_bot, state=tk.DISABLED)
        self.stop_btn.grid(row=0, column=1, padx=5)

    def start_bot(self):
        self.bot.start()
        self.status_label.config(text="Estado: Escaneando...", foreground="green")
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)

    def stop_bot(self):
        self.bot.stop()
        self.status_label.config(text="Estado: Detenido", foreground="red")
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)