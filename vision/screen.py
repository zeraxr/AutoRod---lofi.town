import mss
import cv2
import numpy as np


class ScreenProcessor:
    """Maneja la captura de pantalla y la visión por computadora."""

    def __init__(self, monitor_region=None):
        self.sct = mss.mss()
        # REGION DE CAPTURA: (top = Y, left = X)
        self.region = monitor_region or {"top": 200, "left": 750, "width": 300, "height": 450}

        # --- COLORES HSV ---
        self.lower_green = np.array([35, 50, 150])
        self.upper_green = np.array([55, 150, 255])

        self.lower_needle = np.array([0, 150, 150])
        self.upper_needle = np.array([15, 255, 255])

        self.lower_text = np.array([0, 0, 240])
        self.upper_text = np.array([180, 15, 255])

    def capture_frame(self):
        img = np.array(self.sct.grab(self.region))
        return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

    def analyze_skill_check(self, frame):
        hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask_green = cv2.inRange(hsv_frame, self.lower_green, self.upper_green)
        mask_needle = cv2.inRange(hsv_frame, self.lower_needle, self.upper_needle)

        overlap = cv2.bitwise_and(mask_green, mask_needle)
        if cv2.countNonZero(overlap) > 5:
            return True
        return False

    def detect_action_buttons(self, frame):
        hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask_text = cv2.inRange(hsv_frame, self.lower_text, self.upper_text)
        if cv2.countNonZero(mask_text) > 100:
            return True
        return False

    def show_preview(self):
        """Muestra en vivo lo que el bot está viendo. Cierra con 'Q' o la 'X'."""
        window_name = "AutoRod - Vista Previa"
        cv2.namedWindow(window_name)

        while True:
            frame = self.capture_frame()
            cv2.imshow(window_name, frame)

            # Romper si se presiona la tecla 'Q'
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

            # Romper si el usuario cierra la ventana con la 'X'
            if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
                break

        cv2.destroyAllWindows()