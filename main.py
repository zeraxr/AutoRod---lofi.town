import tkinter as tk
from tkinter import ttk
import threading
import time
import mss
import cv2
import numpy as np
import pyautogui


class ScreenProcessor:
    """Maneja la captura de pantalla y la visión por computadora."""

    def __init__(self, monitor_region=None):
        # monitor_region es un dict: {'top': 100, 'left': 100, 'width': 400, 'height': 200}
        self.sct = mss.mss()
        # Si no se define región, se captura una porción del centro de la pantalla por defecto
        self.region = monitor_region or {"top": 400, "left": 760, "width": 400, "height": 280}

    def capture_frame(self):
        """Captura la región especificada y la convierte a un formato usable por OpenCV."""
        img = np.array(self.sct.grab(self.region))
        # MSS captura en BGRA, OpenCV usa BGR por defecto
        frame = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        return frame

    def analyze_skill_check(self, frame):
        """
        AQUÍ VA LA LÓGICA DE VISIÓN:
        1. Encontrar la zona verde (filtrado por color HSV).
        2. Encontrar la aguja (Template matching o filtrado de color).
        3. Retornar True si la aguja está dentro de la zona verde.
        """
        # TODO: Implementar análisis real de OpenCV
        # Ejemplo simulado:
        # should_click = True si aguja_x > zona_verde_inicio_x y aguja_x < zona_verde_fin_x
        should_click = False
        return should_click


class ActionController:
    """Maneja las interacciones de hardware (mouse/teclado)."""

    @staticmethod
    def click_fishing_button():
        """Simula el clic para acertar el minijuego."""
        print("[Acción] ¡Clic realizado!")
        pyautogui.click()
        # Si pyautogui no funciona en tu juego, usa:
        # import pydirectinput
        # pydirectinput.click()


class AutoFisherBot:
    """Clase principal que orquesta la lógica del bot en un hilo separado."""

    def __init__(self):
        self.is_running = False
        self.bot_thread = None
        self.screen_processor = ScreenProcessor()
        self.action_controller = ActionController()

    def start(self):
        if not self.is_running:
            self.is_running = True
            self.bot_thread = threading.Thread(target=self._bot_loop, daemon=True)
            self.bot_thread.start()
            print("[Bot] Iniciado.")

    def stop(self):
        self.is_running = False
        print("[Bot] Detenido.")

    def _bot_loop(self):
        """El bucle principal que corre mientras el bot está activo."""
        while self.is_running:
            start_time = time.time()

            # 1. Capturar pantalla
            frame = self.screen_processor.capture_frame()

            # 2. Analizar si la aguja está en lo verde
            should_click = self.screen_processor.analyze_skill_check(frame)

            # 3. Reaccionar
            if should_click:
                self.action_controller.click_fishing_button()
                time.sleep(2)  # Pausa para evitar clics múltiples seguidos (Cooldown)

            # Pequeño delay para no saturar la CPU (aprox 60 FPS)
            time.sleep(max(0, (1 / 60) - (time.time() - start_time)))


class AutoRodGUI:
    """Maneja la interfaz gráfica de usuario usando Tkinter."""

    def __init__(self, root):
        self.root = root
        self.root.title("AutoRod Pro - Fishing Bot")
        self.root.geometry("300x150")
        self.root.resizable(False, False)

        self.bot = AutoFisherBot()

        self._build_ui()

    def _build_ui(self):
        # Título
        title_label = ttk.Label(self.root, text="AutoRod Pro", font=("Helvetica", 16, "bold"))
        title_label.pack(pady=10)

        # Estado
        self.status_label = ttk.Label(self.root, text="Estado: Detenido", foreground="red")
        self.status_label.pack(pady=5)

        # Botones
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


if __name__ == "__main__":
    # Instanciamos la ventana principal y arrancamos el mainloop
    root = tk.Tk()
    app = AutoRodGUI(root)
    root.mainloop()