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
        if cv2.countNonZero(overlap) > 15:
            return True
        return False

    def detect_action_buttons(self, frame):
        hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask_text = cv2.inRange(hsv_frame, self.lower_text, self.upper_text)
        if cv2.countNonZero(mask_text) > 300:
            return True
        return False

    def show_preview(self):
        window_name = "AutoRod - Vista Previa (Rayos X)"
        cv2.namedWindow(window_name)

        while True:
            frame = self.capture_frame()
            hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

            # --- RAYOS X PARA EL BOTON ---
            mask_text = cv2.inRange(hsv_frame, self.lower_text, self.upper_text)
            pixels_text = cv2.countNonZero(mask_text)
            frame[mask_text > 0] = [255, 0, 0]  # Lo que detecte como botón, lo pinta Azul

            if pixels_text > 300:
                cv2.putText(frame, f"BOTON VISTO: {pixels_text}px", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                            (255, 0, 0), 2)

            # --- RAYOS X PARA EL MINIJUEGO ---
            mask_green = cv2.inRange(hsv_frame, self.lower_green, self.upper_green)
            mask_needle = cv2.inRange(hsv_frame, self.lower_needle, self.upper_needle)
            overlap = cv2.bitwise_and(mask_green, mask_needle)
            pixels_overlap = cv2.countNonZero(overlap)

            frame[overlap > 0] = [255, 0, 255]  # Lo que detecte superpuesto, lo pinta Magenta

            if pixels_overlap > 15:
                cv2.putText(frame, f"¡CLIC! AGUJA EN VERDE: {pixels_overlap}px", (10, 60), cv2.FONT_HERSHEY_SIMPLEX,
                            0.6, (255, 0, 255), 2)

            cv2.imshow(window_name, frame)

            # Cerramos esta ventana con 'x' para no chocar con el apagado global
            if cv2.waitKey(1) & 0xFF == ord('x'):
                break
            if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
                break

        cv2.destroyAllWindows()