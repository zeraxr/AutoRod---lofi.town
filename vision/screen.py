import mss
import cv2
import numpy as np


class ScreenProcessor:
    """Maneja la captura de pantalla y la visión por computadora."""

    def __init__(self, monitor_region=None):
        self.sct = mss.mss()
        # REGION DE CAPTURA: (top = Y, left = X)
        self.region = monitor_region or {"top": 300, "left": 600, "width": 600, "height": 600}

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
        """Muestra en vivo lo que el bot está viendo. Presiona 'q' para cerrar."""
        print("[Visión] Abriendo vista previa. Presiona 'q' en la ventana para salir.")
        while True:
            # Capturamos el frame en tiempo real
            frame = self.capture_frame()

            # Mostramos la ventana de OpenCV
            cv2.imshow("AutoRod - Vista Previa (Presiona Q para salir)", frame)

            # cv2.waitKey(1) actualiza la ventana y espera 1ms. Si la tecla es 'q', rompemos el ciclo.
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        # Cerramos la ventana de OpenCV al terminar
        cv2.destroyAllWindows()