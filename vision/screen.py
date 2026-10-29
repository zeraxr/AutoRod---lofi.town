import mss
import cv2
import numpy as np


class ScreenProcessor:
    def __init__(self, monitor_region=None):
        self.sct = mss.mss()
        self.region = monitor_region or {"top": 200, "left": 880, "width": 350, "height": 450}

        self.lower_green = np.array([35, 50, 150])
        self.upper_green = np.array([55, 150, 255])

        self.lower_needle = np.array([0, 150, 150])
        self.upper_needle = np.array([15, 255, 255])

        # --- NUEVOS COLORES PARA EL TEXTO (Más permisivos con los grises) ---
        self.lower_text = np.array([0, 0, 180])
        self.upper_text = np.array([180, 40, 255])

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
        """Muestra la vista previa con diagnóstico en tiempo real (HUD)."""
        window_name = "AutoRod - Vista Previa (Modo Debug)"
        cv2.namedWindow(window_name)

        while True:
            frame = self.capture_frame()
            hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

            # 1. Diagnóstico del Botón
            mask_text = cv2.inRange(hsv_frame, self.lower_text, self.upper_text)
            pixels_text = cv2.countNonZero(mask_text)

            if pixels_text > 100:
                cv2.putText(frame, f"BOTON VISTO! ({pixels_text} px)", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                            (0, 255, 0), 2)
            else:
                cv2.putText(frame, f"Ciego... ({pixels_text} px)", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255),
                            2)

            # 2. Diagnóstico del Minijuego
            mask_green = cv2.inRange(hsv_frame, self.lower_green, self.upper_green)
            mask_needle = cv2.inRange(hsv_frame, self.lower_needle, self.upper_needle)
            pixels_overlap = cv2.countNonZero(cv2.bitwise_and(mask_green, mask_needle))

            if pixels_overlap > 5:
                cv2.putText(frame, f"¡HACIENDO CLIC! ({pixels_overlap} px)", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                            (255, 0, 0), 2)

            cv2.imshow(window_name, frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
                break

        cv2.destroyAllWindows()