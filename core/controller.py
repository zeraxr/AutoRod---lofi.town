import pyautogui
import time

class ActionController:
    """Maneja las interacciones de hardware (mouse/teclado)."""
    @staticmethod
    def click_fishing_button():
        # Simula un clic humano manteniendo presionado 50 milisegundos
        pyautogui.mouseDown()
        time.sleep(0.05)
        pyautogui.mouseUp()