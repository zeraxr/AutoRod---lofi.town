import unittest
import cv2
import numpy as np
from autorod.domain.models.image_payload import ImagePayload, PixelFormat
from autorod.infrastructure.vision.geometric_strategy import GeometricVisionStrategy
from autorod.infrastructure.templates.file_repository import FileTemplateRepository


class TestMinigameAssetsVision(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = FileTemplateRepository()
        self.strategy = GeometricVisionStrategy(template_repo=self.repo)

    def test_dial_template_detected_on_real_minigame_dial(self) -> None:
        # Load minigame_dial_1
        payload_dial = self.repo.load("minigame_dial_1")
        # Embed in a canvas
        canvas = np.full((600, 800, 3), 40, dtype=np.uint8)
        dh, dw = payload_dial.height, payload_dial.width
        raw_mat = np.frombuffer(payload_dial.data, dtype=np.uint8).reshape((dh, dw, 3))
        canvas[150:150+dh, 200:200+dw] = raw_mat

        test_payload = ImagePayload(
            width=800,
            height=600,
            pixel_format=PixelFormat.BGR8,
            stride=800 * 3,
            data=canvas.tobytes(),
            frame_id=1,
            captured_at_ns=0,
            source_id="test_dial"
        )
        res = self.strategy.analyze(test_payload)
        self.assertTrue(res.found)
        self.assertEqual(res.strategy_id, "minigame_needle_hit")
        self.assertIsNotNone(res.center)
        self.assertAlmostEqual(res.center.x, 200 + dw // 2, delta=5)  # type: ignore
        self.assertAlmostEqual(res.center.y, 150 + dh // 2, delta=5)  # type: ignore

    def test_blank_card_detected_on_real_card_asset(self) -> None:
        payload_card = self.repo.load("blank_card")
        res = self.strategy.analyze(payload_card)
        self.assertTrue(res.found)
        self.assertEqual(res.strategy_id, "blank_card_detected")
        self.assertIsNotNone(res.center)
        self.assertIsNotNone(res.region)
        self.assertGreater(res.region.size.width, 250)  # type: ignore

    def test_dial_detected_and_tracking_when_needle_not_aligned(self) -> None:
        payload_dial = self.repo.load("minigame_dial_1")
        canvas = np.full((600, 800, 3), 40, dtype=np.uint8)
        dh, dw = payload_dial.height, payload_dial.width
        raw_mat = np.frombuffer(payload_dial.data, dtype=np.uint8).reshape((dh, dw, 3))
        # Rotar 180 grados para que el sector verde quede abajo
        rotated_mat = cv2.rotate(raw_mat, cv2.ROTATE_180)
        canvas[150:150+dh, 200:200+dw] = rotated_mat

        test_payload = ImagePayload(
            width=800,
            height=600,
            pixel_format=PixelFormat.BGR8,
            stride=800 * 3,
            data=canvas.tobytes(),
            frame_id=2,
            captured_at_ns=0,
            source_id="test_dial_rot"
        )
        res = self.strategy.analyze(test_payload)
        self.assertFalse(res.found)
        self.assertEqual(res.strategy_id, "minigame_tracking")
        self.assertIsNotNone(res.center)
        self.assertAlmostEqual(res.center.x, 200 + dw // 2, delta=5)  # type: ignore
        self.assertAlmostEqual(res.center.y, 150 + dh // 2, delta=5)  # type: ignore

    def test_dial_fast_track_roi_on_consecutive_frames(self) -> None:
        payload_dial = self.repo.load("minigame_dial_1")
        canvas = np.full((600, 800, 3), 40, dtype=np.uint8)
        dh, dw = payload_dial.height, payload_dial.width
        raw_mat = np.frombuffer(payload_dial.data, dtype=np.uint8).reshape((dh, dw, 3))
        canvas[150:150+dh, 200:200+dw] = raw_mat

        test_payload = ImagePayload(
            width=800,
            height=600,
            pixel_format=PixelFormat.BGR8,
            stride=800 * 3,
            data=canvas.tobytes(),
            frame_id=1,
            captured_at_ns=0,
            source_id="test_dial"
        )
        # Frame 1: Detección inicial (guarda _last_dial_roi)
        res1 = self.strategy.analyze(test_payload)
        self.assertTrue(res1.found)
        self.assertIsNotNone(self.strategy._last_dial_roi)

        # Frame 2: Rastreo ultra-rápido por ROI (< 0.2 ms)
        res2 = self.strategy.analyze(test_payload)
        self.assertTrue(res2.found)
        self.assertEqual(res2.strategy_id, "minigame_needle_hit")
        self.assertAlmostEqual(res2.center.x, 200 + dw // 2, delta=5)  # type: ignore

    def test_blank_card_detected_at_various_zoom_levels(self) -> None:
        """Verifica que la tarjeta de recompensa se detecte tanto en zoom reducido (0.50x) como aumentado (1.50x)."""
        card_raw = self.repo.load("blank_card")
        cdh, cdw = card_raw.height, card_raw.width
        raw_mat = np.frombuffer(card_raw.data, dtype=np.uint8).reshape((cdh, cdw, 3))

        for zoom in (0.50, 1.0, 1.50):
            scaled_card = cv2.resize(raw_mat, (int(cdw * 0.5 * zoom), int(cdh * 0.5 * zoom)), interpolation=cv2.INTER_LINEAR)
            zh, zw = scaled_card.shape[:2]

            canvas = np.full((1080, 1920, 3), 40, dtype=np.uint8)
            canvas[300:300+zh, 500:500+zw] = scaled_card
            payload = ImagePayload(
                width=1920,
                height=1080,
                pixel_format=PixelFormat.BGR8,
                stride=1920 * 3,
                data=canvas.tobytes(),
                frame_id=10,
                captured_at_ns=0,
                source_id=f"card_zoom_{zoom}"
            )
            res = self.strategy.analyze(payload)
            self.assertTrue(res.found, f"Fallo al detectar blank_card a zoom {zoom}x")
            self.assertEqual(res.strategy_id, "blank_card_detected")
            self.assertIsNotNone(res.center)
            # El centro del contorno blanco en blank_card.png está en (244, 246)
            expected_cx = 500 + int(244 * 0.5 * zoom)
            expected_cy = 300 + int(246 * 0.5 * zoom)
            self.assertAlmostEqual(res.center.x, expected_cx, delta=6)  # type: ignore
            self.assertAlmostEqual(res.center.y, expected_cy, delta=6)  # type: ignore

    def test_minigame_dial_inherits_button_scale_and_detects_zoomed_dial(self) -> None:
        """Verifica que el dial herede la escala memorizada por los botones y se detecte con zoom 1.25x."""
        self.strategy.clear_scale_cache()
        self.strategy._cached_button_scale = 1.25

        payload_dial = self.repo.load("minigame_dial_1")
        dh, dw = payload_dial.height, payload_dial.width
        raw_mat = np.frombuffer(payload_dial.data, dtype=np.uint8).reshape((dh, dw, 3))

        scaled_dial = cv2.resize(raw_mat, (int(dw * 1.25), int(dh * 1.25)), interpolation=cv2.INTER_LINEAR)
        sdh, sdw = scaled_dial.shape[:2]

        canvas = np.full((720, 1280, 3), 40, dtype=np.uint8)
        canvas[200:200+sdh, 400:400+sdw] = scaled_dial

        test_payload = ImagePayload(
            width=1280,
            height=720,
            pixel_format=PixelFormat.BGR8,
            stride=1280 * 3,
            data=canvas.tobytes(),
            frame_id=20,
            captured_at_ns=0,
            source_id="test_dial_zoomed"
        )
        res = self.strategy.analyze(test_payload)
        self.assertTrue(res.found)
        self.assertEqual(res.strategy_id, "minigame_needle_hit")
        self.assertEqual(self.strategy._cached_dial_scale, 1.25)


if __name__ == "__main__":
    unittest.main()
