import mss
import cv2
import numpy as np
import os


class ScreenProcessor:
    def __init__(self, monitor_region=None):
        self.sct = mss.mss()
        # Ajusta esta región si es necesario para encuadrar todo
        self.region = monitor_region or {"top": 200, "left": 880, "width": 350, "height": 450}

        # --- 1. CARGAR TEMPLATES DE ACCIÓN (Lanzar/Recoger) ---
        self.action_templates = []
        for file in ["template_cast.png", "template_reel.png"]:
            if os.path.exists(file):
                img = cv2.imread(file, cv2.IMREAD_COLOR)
                self.action_templates.append({"name": file, "image": img})
            else:
                print(f"[Aviso] No se encontró {file}")

        # --- 2. CARGAR TEMPLATE DEL MINIJUEGO (Aguja sobre verde) ---
        self.minigame_template = None
        if os.path.exists("template_minigame.png"):
            self.minigame_template = cv2.imread("template_minigame.png", cv2.IMREAD_COLOR)
        else:
            print("[Aviso] No se encontró template_minigame.png")

    def capture_frame(self):
        img = np.array(self.sct.grab(self.region))
        return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

    def analyze_skill_check(self, frame):
        """Busca el recorte exacto de la aguja tocando lo verde."""
        if self.minigame_template is None:
            return False

        res = cv2.matchTemplate(frame, self.minigame_template, cv2.TM_CCOEFF_NORMED)
        # 0.85 = 85% de similitud. Es alto para evitar clics accidentales.
        if len(np.where(res >= 0.85)[0]) > 0:
            return True
        return False

    def detect_action_buttons(self, frame):
        """Busca los botones CAST o REEL."""
        if not self.action_templates:
            return False

        for tmpl in self.action_templates:
            res = cv2.matchTemplate(frame, tmpl["image"], cv2.TM_CCOEFF_NORMED)
            if len(np.where(res >= 0.8)[0]) > 0:
                return True
        return False

    def show_preview(self):
        window_name = "AutoRod - Vista Previa (Patrones SOTA)"
        cv2.namedWindow(window_name)

        while True:
            frame = self.capture_frame()

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
                loc = np.where(res >= 0.85)
                h, w = self.minigame_template.shape[:2]

                match_count = len(loc[0])
                for pt in zip(*loc[::-1]):
                    # Dibuja un rectángulo Magenta justo donde encaje la aguja
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