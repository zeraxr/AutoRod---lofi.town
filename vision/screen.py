import mss
import cv2
import numpy as np


class ScreenProcessor:
    """Maneja la captura de pantalla y la visión por computadora."""

    def __init__(self, monitor_region=None):
        self.sct = mss.mss()
        # REGION DE CAPTURA: Deberás ajustar esto para que encuadre el círculo del minijuego en tu pantalla.
        self.region = monitor_region or {"top": 300, "left": 600, "width": 600, "height": 600}

        # --- COLORES HSV PARA TU JUEGO ---
        # 1. Zona Segura (Verde Claro / Pistacho)
        self.lower_green = np.array([35, 50, 150])
        self.upper_green = np.array([55, 150, 255])

        # 2. Aguja (Rojo / Naranja)
        self.lower_needle = np.array([0, 150, 150])
        self.upper_needle = np.array([15, 255, 255])

        # 3. Botones (CAST! / REEL!) - Blanco con reborde oscuro
        # Detectaremos el blanco puro del interior de las letras
        self.lower_text = np.array([0, 0, 240])
        self.upper_text = np.array([180, 15, 255])

    def capture_frame(self):
        img = np.array(self.sct.grab(self.region))
        return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

    def analyze_skill_check(self, frame):
        """Analiza la superposición entre la aguja y la zona verde."""
        hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # Crear máscaras
        mask_green = cv2.inRange(hsv_frame, self.lower_green, self.upper_green)
        mask_needle = cv2.inRange(hsv_frame, self.lower_needle, self.upper_needle)

        # Truco mágico: Intersección lógica (Bitwise AND)
        # Esto crea una nueva imagen donde SOLO hay píxeles si la aguja y el verde coinciden en el mismo lugar
        overlap = cv2.bitwise_and(mask_green, mask_needle)

        # Contamos cuántos píxeles se están superponiendo
        overlap_pixels = cv2.countNonZero(overlap)

        # Si hay un número razonable de píxeles superpuestos (ej. más de 5), significa que la aguja tocó el verde
        if overlap_pixels > 5:
            # print(f"¡CLIC! Intersección detectada: {overlap_pixels} píxeles.")
            return True

        return False

    def detect_action_buttons(self, frame):
        """Busca el texto blanco brillante de los botones CAST y REEL."""
        hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask_text = cv2.inRange(hsv_frame, self.lower_text, self.upper_text)

        # Si hay muchos píxeles blancos concentrados, es probable que esté el botón en pantalla
        if cv2.countNonZero(mask_text) > 100:
            return True
        return False