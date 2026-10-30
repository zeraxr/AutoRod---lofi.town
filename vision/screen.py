import mss
import cv2
import numpy as np
import os


class ScreenProcessor:
    def __init__(self, monitor_region=None):
        self.sct = mss.mss()
        self.region = monitor_region or {"top": 200, "left": 880, "width": 350, "height": 450}

        # --- 1. CARGAR TEMPLATES DE ACCIÓN ---
        self.action_templates = []
        for file in ["template_cast.png", "template_reel.png"]:
            if os.path.exists(file):
                img = cv2.imread(file, cv2.IMREAD_COLOR)
                self.action_templates.append({"name": file, "image": img})
            else:
                print(f"[Aviso] No se encontró {file}")

        # --- 2. CARGAR TEMPLATE DEL MINIJUEGO ---
        self.minigame_template = None
        if os.path.exists("template_minigame.png"):
            self.minigame_template = cv2.imread("template_minigame.png", cv2.IMREAD_COLOR)
        else:
            print("[Aviso] No se encontró template_minigame.png")

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
        """Detecta una gran masa de píxeles blancos (la tarjeta del pescado)."""
        hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        # Rango para blanco puro
        lower_white = np.array([0, 0, 240])
        upper_white = np.array([180, 15, 255])
        mask_white = cv2.inRange(hsv_frame, lower_white, upper_white)

        # Si la tarjeta cubre gran parte de la pantalla (ej. > 15,000 píxeles blancos)
        if cv2.countNonZero(mask_white) > 15000:
            return True
        return False

    def show_preview(self):
        window_name = "AutoRod - Vista Previa (Patrones SOTA)"
        cv2.namedWindow(window_name)

        while True:
            frame = self.capture_frame()

            # --- DIAGNÓSTICO DE TARJETA DE RECOMPENSA ---
            hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            mask_white = cv2.inRange(hsv_frame, np.array([0, 0, 240]), np.array([180, 15, 255]))
            pixels_white = cv2.countNonZero(mask_white)

            if pixels_white > 15000:
                cv2.putText(frame, f"TARJETA DETECTADA! ({pixels_white}px)", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6,
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