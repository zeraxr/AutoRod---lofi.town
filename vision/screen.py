import mss
import cv2
import numpy as np
import os
import sys


def resource_path(relative_path):
    """Obtiene la ruta absoluta, funciona en desarrollo y dentro del .exe de PyInstaller"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


class ScreenProcessor:
    def __init__(self, monitor_region=None):
        self.sct = mss.mss()
        monitor = self.sct.monitors[1]

        # 1. Obtener la resolución actual del usuario
        screen_w = monitor["width"]
        screen_h = monitor["height"]

        # 2. Calcular la proporción basada en tu monitor original (1920x1080)
        ratio_x = screen_w / 1920
        ratio_y = screen_h / 1080

        # 3. Aplicar las coordenadas matemáticas proporcionales
        self.region = monitor_region or {
            "top": int(200 * ratio_y),
            "left": int(880 * ratio_x),
            "width": int(350 * ratio_x),
            "height": int(450 * ratio_y)
        }

        # 4. Umbral matemático para la tarjeta (10% del área capturada)
        self.white_threshold = int(self.region["width"] * self.region["height"] * 0.10)

        # --- CARGAR TEMPLATES DE ACCIÓN ---
        self.action_templates = []
        for file in ["template_cast.png", "template_reel.png"]:
            path = resource_path(f"materials/{file}")
            if os.path.exists(path):
                img = cv2.imread(path, cv2.IMREAD_COLOR)
                self.action_templates.append({"name": file, "image": img})
            else:
                print(f"[Aviso] No se encontró {path}")

        # --- CARGAR TEMPLATE DEL MINIJUEGO ---
        self.minigame_template = None
        minigame_path = resource_path("materials/template_minigame.png")
        if os.path.exists(minigame_path):
            self.minigame_template = cv2.imread(minigame_path, cv2.IMREAD_COLOR)
        else:
            print(f"[Aviso] No se encontró {minigame_path}")

    def capture_frame(self):
        img = np.array(self.sct.grab(self.region))
        return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

    def analyze_skill_check(self, frame):
        if self.minigame_template is None:
            return False

        res = cv2.matchTemplate(frame, self.minigame_template, cv2.TM_CCOEFF_NORMED)
        if len(np.where(res >= 0.97)[0]) > 0:
            return True
        return False

    def detect_action_buttons(self, frame):
        if not self.action_templates:
            return False

        for tmpl in self.action_templates:
            res = cv2.matchTemplate(frame, tmpl["image"], cv2.TM_CCOEFF_NORMED)
            if len(np.where(res >= 0.8)[0]) > 0:
                return True
        return False

    def detect_reward_card(self, frame):
        hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        lower_white = np.array([0, 0, 240])
        upper_white = np.array([180, 15, 255])
        mask_white = cv2.inRange(hsv_frame, lower_white, upper_white)

        # Usamos el umbral dinámico calculado en el __init__
        if cv2.countNonZero(mask_white) > self.white_threshold:
            return True
        return False

    def show_preview(self):
        window_name = "AutoRod - Vista Previa (Patrones SOTA)"
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

        while True:
            frame = self.capture_frame()

            # --- DIAGNÓSTICO DE TARJETA DE RECOMPENSA ---
            hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            mask_white = cv2.inRange(hsv_frame, np.array([0, 0, 240]), np.array([180, 15, 255]))
            pixels_white = cv2.countNonZero(mask_white)

            if pixels_white > self.white_threshold:
                cv2.putText(frame, f"TARJETA! ({pixels_white}/{self.white_threshold}px)", (10, 90),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                            (0, 255, 255), 2)

            # --- DIAGNÓSTICO DE BOTONES DE ACCIÓN ---
            for tmpl in self.action_templates:
                res = cv2.matchTemplate(frame, tmpl["image"], cv2.TM_CCOEFF_NORMED)
                loc = np.where(res >= 0.8)
                h, w = tmpl["image"].shape[:2]

                for pt in zip(*loc[::-1]):
                    cv2.rectangle(frame, pt, (pt[0] + w, pt[1] + h), (255, 0, 0), 2)
                    cv2.putText(frame, tmpl["name"], (pt[0], pt[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)

            # --- DIAGNÓSTICO DEL MINIJUEGO ---
            if self.minigame_template is not None:
                res = cv2.matchTemplate(frame, self.minigame_template, cv2.TM_CCOEFF_NORMED)
                loc = np.where(res >= 0.97)
                h, w = self.minigame_template.shape[:2]

                match_count = len(loc[0])
                for pt in zip(*loc[::-1]):
                    cv2.rectangle(frame, pt, (pt[0] + w, pt[1] + h), (255, 0, 255), 2)

                if match_count > 0:
                    cv2.putText(frame, "¡CLIC! PATRON PERFECTO", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 255),
                                2)

            cv2.imshow(window_name, frame)

            if cv2.waitKey(1) & 0xFF == ord('x'):
                break
            if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
                break

        cv2.destroyAllWindows()