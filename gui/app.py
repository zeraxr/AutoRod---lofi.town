import tkinter as tk
from tkinter import ttk
import threading
import keyboard
import time
from core.bot import AutoFisherBot


class AutoRodGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("AutoRod Pro")
        self.root.geometry("320x150")
        self.root.resizable(False, False)

        self.bot = AutoFisherBot()
        self._build_ui()

        # Inicia el vigilante de teclado en un hilo de fondo
        threading.Thread(target=self._global_key_listener, daemon=True).start()

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

        self.preview_btn = ttk.Button(button_frame, text="Ver Región", command=self.show_preview)
        self.preview_btn.grid(row=0, column=2, padx=5)

    def _global_key_listener(self):
        """Vigila si el usuario presiona 'q' para matar el programa."""
        while True:
            if keyboard.is_pressed('q'):
                print("[Sistema] Tecla Q presionada. Apagando motor...")
                self.root.after(0, self.quit_app)
                break
            time.sleep(0.1)

    def quit_app(self):
        """Detiene el bot y cierra la ventana por completo."""
        self.bot.stop()
        self.root.destroy()

    def start_bot(self):
        self.bot.start()
        self.status_label.config(text="Estado: Escaneando...", foreground="green")
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.preview_btn.config(state=tk.DISABLED)

    def stop_bot(self):
        self.bot.stop()
        self.status_label.config(text="Estado: Detenido", foreground="red")
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.preview_btn.config(state=tk.NORMAL)

    def show_preview(self):
        self.status_label.config(text="Estado: Vista Previa", foreground="blue")
        self.start_btn.config(state=tk.DISABLED)
        self.preview_btn.config(state=tk.DISABLED)
        threading.Thread(target=self._run_preview_thread, daemon=True).start()

    def _run_preview_thread(self):
        self.bot.screen_processor.show_preview()
        self.root.after(0, self._restore_ui)

    def _restore_ui(self):
        self.status_label.config(text="Estado: Detenido", foreground="red")
        self.start_btn.config(state=tk.NORMAL)
        self.preview_btn.config(state=tk.NORMAL)