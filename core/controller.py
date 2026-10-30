import pyautogui
import time

class ActionController:
    """Maneja las interacciones de hardware (mouse/teclado)."""
    @staticmethod
    def click_fishing_button():
        pyautogui.mouseDown()
        time.sleep(0.05)
        pyautogui.mouseUp()

    @staticmethod
    def spam_click(clicks=5):
        """Dispara una ráfaga de clics firmes para saltar tarjetas o diálogos."""
        for _ in range(clicks):
            pyautogui.mouseDown()
            time.sleep(0.05)  # Mantenemos presionado más tiempo (50ms)
            pyautogui.mouseUp()
            time.sleep(0.05)  # Pausa entre clics