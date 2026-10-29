import pyautogui

class ActionController:
    """Maneja las interacciones de hardware (mouse/teclado)."""
    @staticmethod
    def click_fishing_button():
        print("[Acción] ¡Clic simulado!")
        pyautogui.click()