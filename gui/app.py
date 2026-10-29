import tkinter as tk
from tkinter import ttk
import threading
from core.bot import AutoFisherBot


class AutoRodGUI:
    """Maneja la interfaz gráfica de usuario."""

    def __init__(self, root):
        self.root = root
        self.root.title("AutoRod Pro")
        self.root.geometry("320x150")  # Ampliamos un poco el ancho para el tercer botón
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

        self.preview_btn = ttk.Button(button_frame, text="Ver Región", command=self.show_preview)
        self.preview_btn.grid(row=0, column=2, padx=5)

    def start_bot(self):
        self.bot.start()
        self.status_label.config(text="Estado: Escaneando...", foreground="green")
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.preview_btn.config(state=tk.DISABLED)  # Desactivar vista previa mientras pesca

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

        # Ejecutamos la vista previa en un hilo para que la ventanita de Tkinter no se congele
        threading.Thread(target=self._run_preview_thread, daemon=True).start()

    def _run_preview_thread(self):
        # Llama a OpenCV (esto abrirá una ventana nueva)
        self.bot.screen_processor.show_preview()

        # Cuando el usuario presione 'q' y se cierre la ventana, reactivamos los botones
        self.status_label.config(text="Estado: Detenido", foreground="red")
        self.start_btn.config(state=tk.NORMAL)
        self.preview_btn.config(state=tk.NORMAL)