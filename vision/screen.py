import mss
import cv2
import numpy as np

class ScreenProcessor:
    """Maneja la captura de pantalla y la visión por computadora."""
    def __init__(self, monitor_region=None):
        self.sct = mss.mss()
        self.region = monitor_region or {"top": 400, "left": 760, "width": 400, "height": 280}

    def capture_frame(self):
        img = np.array(self.sct.grab(self.region))
        return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

    def analyze_skill_check(self, frame):
        # TODO: Aquí irá la matemática de OpenCV
        return False