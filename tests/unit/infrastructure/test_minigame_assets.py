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

    def test_dial_shake_and_red_flash_resilience_on_accidental_miss(self) -> None:
        payload_dial = self.repo.load("minigame_dial_1")
        dh, dw = payload_dial.height, payload_dial.width
        raw_mat = np.frombuffer(payload_dial.data, dtype=np.uint8).reshape((dh, dw, 3))

        canvas = np.full((600, 800, 3), 40, dtype=np.uint8)
        canvas[150:150+dh, 200:200+dw] = raw_mat

        def make_payload(img: np.ndarray, fid: int) -> ImagePayload:
            return ImagePayload(
                width=800, height=600, pixel_format=PixelFormat.BGR8,
                stride=800 * 3, data=img.tobytes(), frame_id=fid,
                captured_at_ns=0, source_id="shake_test"
            )

        # 1. Fotograma Normal (Detección inicial exitosa)
        res1 = self.strategy.analyze(make_payload(canvas, 1))
        self.assertTrue(res1.found)
        self.assertEqual(res1.strategy_id, "minigame_needle_hit")
        saved_roi = self.strategy._last_dial_roi
        self.assertIsNotNone(saved_roi)

        # 2. Fotograma con Destello Rojo de Fallo Accidental (Animación de fallo en lofi.town)
        red_canvas = canvas.copy()
        red_canvas[150:150+dh, 200:200+dw, 2] = np.clip(
            red_canvas[150:150+dh, 200:200+dw, 2].astype(int) + 110, 0, 255
        )
        res2 = self.strategy.analyze(make_payload(red_canvas, 2))
        self.assertFalse(res2.found, "Durante el destello rojo no debe pulsar")
        self.assertEqual(res2.strategy_id, "minigame_tracking", "Debe mantenerse rastreando el dial")
        self.assertIsNotNone(self.strategy._last_dial_roi, "El ROI del dial NO debe perderse por el flash rojo")

        # 3. Fotograma con Sacudida (Shake Animation: desplazamiento +-8px y desenfoque)
        shake_canvas = np.full((600, 800, 3), 40, dtype=np.uint8)
        # Desplazar dial por sacudida
        shake_canvas[150-4:150-4+dh, 200+8:200+8+dw] = red_canvas[150:150+dh, 200:200+dw]
        res3 = self.strategy.analyze(make_payload(shake_canvas, 3))
        self.assertFalse(res3.found)
        self.assertEqual(res3.strategy_id, "minigame_tracking")
        self.assertIsNotNone(self.strategy._last_dial_roi, "El ROI del dial NO debe perderse por sacudidas")

        # 4. Fotograma con Dial en Rotación Normal tras Sacudida (Recuperación)
        rot_canvas = np.full((600, 800, 3), 40, dtype=np.uint8)
        rot_canvas[150:150+dh, 200:200+dw] = cv2.rotate(raw_mat, cv2.ROTATE_180)
        res4 = self.strategy.analyze(make_payload(rot_canvas, 4))
        self.assertFalse(res4.found)
        self.assertEqual(res4.strategy_id, "minigame_tracking")
        self.assertIsNotNone(self.strategy._last_dial_roi)

        # 5. Fotograma de Impacto Siguiente (Verde alineado con la aguja)
        res5 = self.strategy.analyze(make_payload(canvas, 5))
        self.assertTrue(res5.found)
        self.assertEqual(res5.strategy_id, "minigame_needle_hit")

    def test_dial_tracking_grace_window_cleans_up_after_full_exit(self) -> None:
        payload_dial = self.repo.load("minigame_dial_1")
        dh, dw = payload_dial.height, payload_dial.width
        raw_mat = np.frombuffer(payload_dial.data, dtype=np.uint8).reshape((dh, dw, 3))

        canvas = np.full((600, 800, 3), 40, dtype=np.uint8)
        canvas[150:150+dh, 200:200+dw] = raw_mat

        def make_payload(img: np.ndarray, fid: int) -> ImagePayload:
            return ImagePayload(
                width=800, height=600, pixel_format=PixelFormat.BGR8,
                stride=800 * 3, data=img.tobytes(), frame_id=fid,
                captured_at_ns=0, source_id="grace_test"
            )

        # Iniciar rastreo
        res1 = self.strategy.analyze(make_payload(canvas, 1))
        self.assertTrue(res1.found)
        self.assertIsNotNone(self.strategy._last_dial_roi)

        # Simular pantalla vacía (minijuego terminó o pez escapó)
        empty_canvas = np.full((600, 800, 3), 40, dtype=np.uint8)

        # Durante la ventana de gracia (< 35 frames), el ROI persiste
        for f in range(2, 30):
            self.strategy.analyze(make_payload(empty_canvas, f))
        self.assertIsNotNone(self.strategy._last_dial_roi)

        # Tras expirar la ventana de gracia (> 35 frames), el ROI se purga limpiamente
        for f in range(30, 42):
            self.strategy.analyze(make_payload(empty_canvas, f))
        self.assertIsNone(self.strategy._last_dial_roi)


if __name__ == "__main__":
    unittest.main()
