import threading
import time
from vision.screen import ScreenProcessor
from core.controller import ActionController


class AutoFisherBot:
    """Orquesta la lógica del bot en un hilo separado."""

    def __init__(self):
        self.is_running = False
        self.bot_thread = None
        self.screen_processor = ScreenProcessor()
        self.action_controller = ActionController()

    def start(self):
        if not self.is_running:
            self.is_running = True
            self.bot_thread = threading.Thread(target=self._bot_loop, daemon=True)
            self.bot_thread.start()
            print("[Bot] Iniciado.")

    def stop(self):
        self.is_running = False
        print("[Bot] Detenido.")

    def _bot_loop(self):
        while self.is_running:
            start_time = time.time()
            frame = self.screen_processor.capture_frame()

            if self.screen_processor.analyze_skill_check(frame):
                self.action_controller.click_fishing_button()
                time.sleep(2)  # Cooldown tras pescar

            time.sleep(max(0, (1 / 60) - (time.time() - start_time)))