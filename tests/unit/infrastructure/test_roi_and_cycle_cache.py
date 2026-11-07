import cv2
import unittest
from pathlib import Path
import numpy as np

from autorod.config import AppConfig
from autorod.domain.models.image_payload import ImagePayload, PixelFormat
from autorod.domain.models.geometry import Point, Size, Region
from autorod.domain.models.match_result import MatchResult
from autorod.domain.models.fishing_state import FishingState, FishingStateMachine
from autorod.application.use_cases.find_and_click import FindAndClickTask
from autorod.infrastructure.capture.mss_capture import MssCaptureSource
from autorod.infrastructure.vision.geometric_strategy import GeometricVisionStrategy
from autorod.infrastructure.templates.file_repository import FileTemplateRepository
from autorod.infrastructure.imaging.numpy_bridge import payload_to_ndarray


class TestRoiAndCycleCache(unittest.TestCase):
    def test_app_config_scan_region_calculation(self) -> None:
        cfg = AppConfig(
            scan_region_enabled=True,
            scan_x1=840,
            scan_y1=540,
            scan_x2=1076,
            scan_y2=246,
        )
        region = cfg.get_scan_region()
        self.assertIsNotNone(region)
        self.assertEqual(region["top"], 246)
        self.assertEqual(region["left"], 840)
        self.assertEqual(region["width"], 236)
        self.assertEqual(region["height"], 294)

        # Si está deshabilitado, debe retornar None
        cfg_disabled = AppConfig(scan_region_enabled=False)
        self.assertIsNone(cfg_disabled.get_scan_region())

        # Configuración por defecto calibrada y centrada (574x454 px)
        cfg_default = AppConfig()
        def_region = cfg_default.get_scan_region()
        self.assertIsNotNone(def_region)
        self.assertEqual(def_region["left"], 670)
        self.assertEqual(def_region["top"], 246)
        self.assertEqual(def_region["width"], 574)
        self.assertEqual(def_region["height"], 454)

    def test_mss_capture_custom_region_property(self) -> None:
        cap = MssCaptureSource(monitor_index=1, region={"top": 246, "left": 840, "width": 236, "height": 294})
        self.assertEqual(cap.custom_region, {"top": 246, "left": 840, "width": 236, "height": 294})
        cap.set_region(None)
        self.assertIsNone(cap.custom_region)

    def test_find_and_click_notifies_cycle_completion(self) -> None:
        completed_cycles: list[int] = []

        def on_cycle(count: int) -> None:
            completed_cycles.append(count)

        fsm = FishingStateMachine(minigame_timeout_s=5.0, card_timeout_s=3.0)
        task = FindAndClickTask(
            click_cooldown_s=0.0,
            minigame_cooldown_s=0.0,
            card_dismiss_duration_s=1.0,
            card_initial_delay_s=0.0,
            card_cooldown_s=0.0,
            max_card_dismiss_clicks=1,
            state_machine=fsm,
            on_cycle_completed=on_cycle,
        )

        def make_res(strategy_id: str, found: bool = True) -> MatchResult:
            return MatchResult(
                found=found,
                confidence=0.9,
                region=Region(top_left=Point(x=100, y=100), size=Size(width=50, height=20)),
                center=Point(x=125, y=110),
                strategy_id=strategy_id,
                frame_id=1,
            )

        # Ciclo 1: Reel -> Minigame -> Card -> Cast (reaparece)
        task.evaluate(make_res("reel_button_detected"))
        self.assertEqual(task.current_state, FishingState.MINIGAME)

        task.evaluate(make_res("minigame_needle_hit"))
        task.evaluate(make_res("blank_card_detected"))
        self.assertEqual(task.current_state, FishingState.CARD_DISMISS)

        # Cuando el botón CAST reaparece y se acciona, el ciclo se considera exitoso
        task.evaluate(make_res("cast_button_detected"))
        self.assertEqual(task.current_state, FishingState.SCANNING)
        self.assertEqual(completed_cycles, [1])
        self.assertEqual(task.total_successful_cycles, 1)

    def test_geometric_strategy_locks_cache_after_5_cycles(self) -> None:
        repo = FileTemplateRepository()
        strategy = GeometricVisionStrategy(
            template_repo=repo,
            cache_size_enabled=True,
            required_cycles_to_lock=5
        )

        self.assertFalse(strategy.is_cache_locked)
        self.assertEqual(strategy.successful_cycles, 0)

        tpl_cast = payload_to_ndarray(repo.load("cast_button"))
        th, tw = tpl_cast.shape[:2]
        screen = np.full((600, 800, 3), 45, dtype=np.uint8)
        screen[200:200+th, 300:300+tw] = tpl_cast

        payload = ImagePayload(
            width=800,
            height=600,
            pixel_format=PixelFormat.BGR8,
            stride=800 * 3,
            data=screen.tobytes(),
            frame_id=1,
            captured_at_ns=0,
            source_id="test_screen"
        )

        # Primera detección: la escala se detecta
        res = strategy.analyze(payload)
        self.assertTrue(res.found)
        self.assertEqual(strategy.cached_scale, 1.0)
        self.assertFalse(strategy.is_cache_locked)  # Aún en calibración (< 5 ciclos)

        # Simular 4 ciclos satisfactorios
        for i in range(1, 5):
            strategy.register_successful_cycle(i)
            self.assertFalse(strategy.is_cache_locked)

        # El 5to ciclo exitoso debe bloquear el caché
        strategy.register_successful_cycle(5)
        self.assertTrue(strategy.is_cache_locked)
        self.assertEqual(strategy.successful_cycles, 5)
        self.assertEqual(strategy.cached_scale, 1.0)
        self.assertEqual(strategy.cached_dimensions, (tw, th))

        # Purgar caché debe desbloquear y resetear
        strategy.clear_scale_cache()
        self.assertFalse(strategy.is_cache_locked)
        self.assertEqual(strategy.successful_cycles, 0)
        self.assertIsNone(strategy.cached_scale)
        self.assertIsNone(strategy.cached_dimensions)

    def test_geometric_strategy_inactivity_watchdog_purges_after_timeout(self) -> None:
        import time
        repo = FileTemplateRepository()
        strategy = GeometricVisionStrategy(
            template_repo=repo,
            cache_size_enabled=True,
            required_cycles_to_lock=5,
            cache_inactivity_timeout_s=0.15
        )

        tpl_cast = payload_to_ndarray(repo.load("cast_button"))
        th, tw = tpl_cast.shape[:2]
        screen = np.full((600, 800, 3), 45, dtype=np.uint8)
        screen[200:200+th, 300:300+tw] = tpl_cast

        payload = ImagePayload(
            width=800,
            height=600,
            pixel_format=PixelFormat.BGR8,
            stride=800 * 3,
            data=screen.tobytes(),
            frame_id=1,
            captured_at_ns=0,
            source_id="test_screen"
        )

        strategy.analyze(payload)
        for i in range(1, 6):
            strategy.register_successful_cycle(i)

        self.assertTrue(strategy.is_cache_locked)

        empty_screen = np.full((600, 800, 3), 0, dtype=np.uint8)
        empty_payload = ImagePayload(
            width=800,
            height=600,
            pixel_format=PixelFormat.BGR8,
            stride=800 * 3,
            data=empty_screen.tobytes(),
            frame_id=2,
            captured_at_ns=0,
            source_id="empty_screen"
        )

        strategy.analyze(empty_payload)
        self.assertTrue(strategy.is_cache_locked)

        time.sleep(0.20)

        strategy.analyze(empty_payload)
        self.assertFalse(strategy.is_cache_locked)
        self.assertEqual(strategy.successful_cycles, 0)
        self.assertIsNone(strategy.cached_scale)


    def test_locked_cache_neighborhood_tolerance(self) -> None:
        repo = FileTemplateRepository()
        strategy = GeometricVisionStrategy(
            template_repo=repo,
            cache_size_enabled=True,
            required_cycles_to_lock=5
        )

        tpl_cast = payload_to_ndarray(repo.load("cast_button"))
        th, tw = tpl_cast.shape[:2]
        screen = np.full((600, 800, 3), 45, dtype=np.uint8)
        screen[200:200+th, 300:300+tw] = tpl_cast

        payload = ImagePayload(
            width=800,
            height=600,
            pixel_format=PixelFormat.BGR8,
            stride=800 * 3,
            data=screen.tobytes(),
            frame_id=1,
            captured_at_ns=0,
            source_id="test_screen"
        )

        strategy.analyze(payload)
        for i in range(1, 6):
            strategy.register_successful_cycle(i)
        self.assertTrue(strategy.is_cache_locked)
        self.assertEqual(strategy.cached_scale, 1.0)

        # Escala vecina 0.95 (+-5%) dentro de la tolerancia de vecindad
        tpl_095 = cv2.resize(tpl_cast, (0, 0), fx=0.95, fy=0.95, interpolation=cv2.INTER_AREA)
        h95, w95 = tpl_095.shape[:2]
        screen_095 = np.full((600, 800, 3), 45, dtype=np.uint8)
        screen_095[200:200+h95, 300:300+w95] = tpl_095

        p_095 = ImagePayload(
            width=800,
            height=600,
            pixel_format=PixelFormat.BGR8,
            stride=800 * 3,
            data=screen_095.tobytes(),
            frame_id=2,
            captured_at_ns=0,
            source_id="test_095"
        )
        res = strategy.analyze(p_095)
        self.assertTrue(res.found)
        self.assertEqual(res.strategy_id, "cast_button_detected")
        self.assertTrue(strategy.is_cache_locked)

    def test_locked_cache_fallback_on_drastic_scale_change(self) -> None:
        repo = FileTemplateRepository()
        strategy = GeometricVisionStrategy(
            template_repo=repo,
            cache_size_enabled=True,
            required_cycles_to_lock=5
        )

        tpl_cast = payload_to_ndarray(repo.load("cast_button"))
        th, tw = tpl_cast.shape[:2]
        screen = np.full((600, 800, 3), 45, dtype=np.uint8)
        screen[200:200+th, 300:300+tw] = tpl_cast

        payload = ImagePayload(
            width=800,
            height=600,
            pixel_format=PixelFormat.BGR8,
            stride=800 * 3,
            data=screen.tobytes(),
            frame_id=1,
            captured_at_ns=0,
            source_id="test_screen"
        )

        strategy.analyze(payload)
        for i in range(1, 6):
            strategy.register_successful_cycle(i)
        self.assertTrue(strategy.is_cache_locked)

        # Cambio radical al 70% (0.70x) fuera de la vecindad inmediata
        tpl_070 = cv2.resize(tpl_cast, (0, 0), fx=0.70, fy=0.70, interpolation=cv2.INTER_AREA)
        h70, w70 = tpl_070.shape[:2]
        screen_070 = np.full((600, 800, 3), 45, dtype=np.uint8)
        screen_070[200:200+h70, 300:300+w70] = tpl_070

        p_070 = ImagePayload(
            width=800,
            height=600,
            pixel_format=PixelFormat.BGR8,
            stride=800 * 3,
            data=screen_070.tobytes(),
            frame_id=2,
            captured_at_ns=0,
            source_id="test_070"
        )

        res = strategy.analyze(p_070)
        self.assertTrue(res.found)
        self.assertEqual(res.strategy_id, "cast_button_detected")
        # El fallback multi-escala debe purgar el cache
        self.assertFalse(strategy.is_cache_locked)
        self.assertEqual(strategy.successful_cycles, 0)


if __name__ == "__main__":
    unittest.main()
