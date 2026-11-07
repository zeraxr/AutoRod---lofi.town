import unittest
import numpy as np
import cv2
from autorod.domain.models.image_payload import ImagePayload, PixelFormat
from autorod.infrastructure.vision.geometric_strategy import GeometricVisionStrategy
from autorod.infrastructure.vision.hsv_contour_strategy import HsvContourStrategy
from autorod.infrastructure.vision.template_match_strategy import TemplateMatchStrategy
from autorod.infrastructure.templates.file_repository import FileTemplateRepository
from autorod.infrastructure.imaging.numpy_bridge import payload_to_ndarray


def _create_synthetic_payload(
        width: int,
        height: int,
        draw_green_circle: bool = True,
        circle_center: tuple[int, int] = (50, 50),
        circle_radius: int = 15,
        draw_needle: bool = False,
        needle_center: tuple[int, int] = (50, 50),
        needle_radius: int = 5,
        offset_x: int = 0,
        offset_y: int = 0
) -> ImagePayload:
    """Crea un ImagePayload sintético para pruebas de visión computacional."""
    img = np.zeros((height, width, 3), dtype=np.uint8)
    if draw_green_circle:
        # Verde pistacho: BGR (80, 200, 140) -> HSV aproximado: (75, 150, 200)
        cv2.circle(img, circle_center, circle_radius, (80, 200, 140), -1)

    if draw_needle:
        # Rojo/naranja aguja: BGR (30, 40, 220) -> HSV aproximado: (2, 220, 220)
        cv2.circle(img, needle_center, needle_radius, (30, 40, 220), -1)

    raw_bytes = img.tobytes()
    return ImagePayload(
        width=width,
        height=height,
        pixel_format=PixelFormat.BGR8,
        stride=width * 3,
        data=raw_bytes,
        frame_id=1,
        captured_at_ns=0,
        source_id="synthetic_test",
        offset_x=offset_x,
        offset_y=offset_y
    )


class TestVisionStrategies(unittest.TestCase):

    def setUp(self) -> None:
        self.repo = FileTemplateRepository()

    def test_geometric_strategy_detects_collision(self) -> None:
        strategy = GeometricVisionStrategy(template_repo=self.repo)
        # Aguja superpuesta al sector verde pistacho (colisión)
        frame = _create_synthetic_payload(
            200, 200,
            circle_center=(100, 100), circle_radius=30,
            draw_needle=True, needle_center=(105, 102), needle_radius=8
        )
        res = strategy.analyze(frame)
        self.assertTrue(res.found)
        self.assertGreaterEqual(res.confidence, 0.70)
        self.assertIsNotNone(res.center)
        self.assertAlmostEqual(res.center.x, 100, delta=3)  # type: ignore
        self.assertAlmostEqual(res.center.y, 100, delta=3)  # type: ignore

    def test_geometric_strategy_no_collision_when_far(self) -> None:
        strategy = GeometricVisionStrategy(template_repo=self.repo)
        # Aguja lejos del sector verde pistacho (sin colisión)
        frame = _create_synthetic_payload(
            300, 300,
            circle_center=(60, 60), circle_radius=25,
            draw_needle=True, needle_center=(250, 250), needle_radius=8
        )
        res = strategy.analyze(frame)
        self.assertFalse(res.found)

    def test_geometric_strategy_zoom_invariance(self) -> None:
        """Comprueba que la relación geométrica se mantenga idéntica con zoom 1x y 2x."""
        strategy = GeometricVisionStrategy(template_repo=self.repo)

        # 1x normal
        f_1x = _create_synthetic_payload(
            150, 150,
            circle_center=(75, 75), circle_radius=20,
            draw_needle=True, needle_center=(78, 76), needle_radius=6
        )
        res_1x = strategy.analyze(f_1x)

        # 2x con zoom (dimensiones y radios al doble)
        f_2x = _create_synthetic_payload(
            300, 300,
            circle_center=(150, 150), circle_radius=40,
            draw_needle=True, needle_center=(156, 152), needle_radius=12
        )
        res_2x = strategy.analyze(f_2x)

        self.assertTrue(res_1x.found)
        self.assertTrue(res_2x.found)
        self.assertAlmostEqual(res_1x.center.x, 75, delta=2)  # type: ignore
        self.assertAlmostEqual(res_2x.center.x, 150, delta=3)  # type: ignore

    def test_geometric_strategy_detects_cast_button(self) -> None:
        strategy = GeometricVisionStrategy(template_repo=self.repo)
        tpl_cast = payload_to_ndarray(self.repo.load("cast_button"))
        th, tw = tpl_cast.shape[:2]

        screen = np.full((1080, 1920, 3), 45, dtype=np.uint8)
        # Insertar botón CAST en (600, 400)
        screen[400:400+th, 600:600+tw] = tpl_cast

        payload = ImagePayload(
            width=1920,
            height=1080,
            pixel_format=PixelFormat.BGR8,
            stride=1920 * 3,
            data=screen.tobytes(),
            frame_id=10,
            captured_at_ns=0,
            source_id="desktop_cast"
        )

        res = strategy.analyze(payload)
        self.assertTrue(res.found)
        self.assertEqual(res.strategy_id, "cast_button_detected")
        self.assertGreaterEqual(res.confidence, 0.90)
        self.assertIsNotNone(res.center)
        expected_x = 600 + tw // 2
        expected_y = 400 + th // 2
        self.assertAlmostEqual(res.center.x, expected_x, delta=4)  # type: ignore
        self.assertAlmostEqual(res.center.y, expected_y, delta=4)  # type: ignore

    def test_geometric_strategy_detects_reel_button(self) -> None:
        strategy = GeometricVisionStrategy(template_repo=self.repo)
        tpl_reel = payload_to_ndarray(self.repo.load("reel_button"))
        th, tw = tpl_reel.shape[:2]

        screen = np.full((1080, 1920, 3), 45, dtype=np.uint8)
        # Insertar botón REEL en (850, 520)
        screen[520:520+th, 850:850+tw] = tpl_reel

        payload = ImagePayload(
            width=1920,
            height=1080,
            pixel_format=PixelFormat.BGR8,
            stride=1920 * 3,
            data=screen.tobytes(),
            frame_id=11,
            captured_at_ns=0,
            source_id="desktop_reel"
        )

        res = strategy.analyze(payload)
        self.assertTrue(res.found)
        self.assertEqual(res.strategy_id, "reel_button_detected")
        self.assertGreaterEqual(res.confidence, 0.90)
        self.assertIsNotNone(res.center)
        expected_x = 850 + tw // 2
        expected_y = 520 + th // 2
        self.assertAlmostEqual(res.center.x, expected_x, delta=4)  # type: ignore
        self.assertAlmostEqual(res.center.y, expected_y, delta=4)  # type: ignore

    def test_geometric_strategy_detects_scaled_button(self) -> None:
        strategy = GeometricVisionStrategy(template_repo=self.repo)
        tpl_cast = payload_to_ndarray(self.repo.load("cast_button"))

        # Escalar botón a 1.25x (zoom de navegador)
        scaled = cv2.resize(tpl_cast, (int(tpl_cast.shape[1] * 1.25), int(tpl_cast.shape[0] * 1.25)))
        th, tw = scaled.shape[:2]

        screen = np.full((1080, 1920, 3), 45, dtype=np.uint8)
        screen[450:450+th, 700:700+tw] = scaled

        payload = ImagePayload(
            width=1920,
            height=1080,
            pixel_format=PixelFormat.BGR8,
            stride=1920 * 3,
            data=screen.tobytes(),
            frame_id=12,
            captured_at_ns=0,
            source_id="desktop_scaled"
        )

        res = strategy.analyze(payload)
        self.assertTrue(res.found)
        self.assertIn("button_detected", res.strategy_id)
        self.assertGreaterEqual(res.confidence, 0.85)
        self.assertIsNotNone(res.center)
        self.assertAlmostEqual(res.center.x, 700 + tw // 2, delta=6)  # type: ignore
        self.assertAlmostEqual(res.center.y, 450 + th // 2, delta=6)  # type: ignore

    def test_geometric_strategy_zero_false_positives_on_cluttered_desktop(self) -> None:
        """Verifica que ventanas normales, barras de tareas y fondos oscuros no disparen clics espurios."""
        strategy = GeometricVisionStrategy(template_repo=self.repo)
        screen = np.full((1080, 1920, 3), 35, dtype=np.uint8)

        # Dibujar rectángulos genéricos de interfaz (carpetas, botones de navegador)
        cv2.rectangle(screen, (100, 100), (400, 300), (200, 200, 200), -1)
        cv2.rectangle(screen, (500, 200), (700, 260), (0, 150, 255), -1)
        cv2.rectangle(screen, (800, 800), (1200, 860), (255, 100, 50), -1)

        payload = ImagePayload(
            width=1920,
            height=1080,
            pixel_format=PixelFormat.BGR8,
            stride=1920 * 3,
            data=screen.tobytes(),
            frame_id=13,
            captured_at_ns=0,
            source_id="cluttered_desktop"
        )

        res = strategy.analyze(payload)
        self.assertFalse(res.found)
        self.assertIsNone(res.center)
        self.assertIsNone(res.region)

    def test_geometric_strategy_size_caching_and_recalibration(self) -> None:
        """Verifica que el tamaño se memorice en la primera detección y se limpie con recalibrar."""
        strategy = GeometricVisionStrategy(template_repo=self.repo, cache_size_enabled=True)
        self.assertIsNone(strategy.cached_scale)
        self.assertIsNone(strategy.cached_dimensions)

        tpl_cast = payload_to_ndarray(self.repo.load("cast_button"))
        th, tw = tpl_cast.shape[:2]
        screen = np.full((1080, 1920, 3), 45, dtype=np.uint8)
        screen[300:300+th, 400:400+tw] = tpl_cast

        payload = ImagePayload(
            width=1920,
            height=1080,
            pixel_format=PixelFormat.BGR8,
            stride=1920 * 3,
            data=screen.tobytes(),
            frame_id=20,
            captured_at_ns=0,
            source_id="cache_test"
        )

        # Primera pasada: detecta y memoriza escala
        res = strategy.analyze(payload)
        self.assertTrue(res.found)
        self.assertEqual(strategy.cached_scale, 1.0)
        self.assertEqual(strategy.cached_dimensions, (tw, th))

        # Segunda pasada: utiliza la escala en caché
        res2 = strategy.analyze(payload)
        self.assertTrue(res2.found)
        self.assertEqual(strategy.cached_scale, 1.0)

        # Recalibrar (limpiar caché)
        strategy.clear_scale_cache()
        self.assertIsNone(strategy.cached_scale)
        self.assertIsNone(strategy.cached_dimensions)

    def test_geometric_strategy_dynamic_mode_does_not_cache(self) -> None:
        """Verifica que en modo dinámico continuo no se bloquea la escala."""
        strategy = GeometricVisionStrategy(template_repo=self.repo, cache_size_enabled=False)
        tpl_cast = payload_to_ndarray(self.repo.load("cast_button"))
        th, tw = tpl_cast.shape[:2]
        screen = np.full((1080, 1920, 3), 45, dtype=np.uint8)
        screen[300:300+th, 400:400+tw] = tpl_cast

        payload = ImagePayload(
            width=1920,
            height=1080,
            pixel_format=PixelFormat.BGR8,
            stride=1920 * 3,
            data=screen.tobytes(),
            frame_id=21,
            captured_at_ns=0,
            source_id="dynamic_test"
        )

        res = strategy.analyze(payload)
        self.assertTrue(res.found)
        self.assertIsNone(strategy.cached_scale)
        self.assertIsNone(strategy.cached_dimensions)

    def test_hsv_contour_strategy_detects_target(self) -> None:
        strategy = HsvContourStrategy(
            lower_hsv=(35, 60, 60),
            upper_hsv=(85, 255, 255),
            min_area=50.0
        )
        frame = _create_synthetic_payload(120, 120, circle_center=(60, 60), circle_radius=15)
        result = strategy.analyze(frame)

        self.assertTrue(result.found)
        self.assertIsNotNone(result.center)
        self.assertAlmostEqual(result.center.x, 60, delta=2)  # type: ignore

    def test_template_match_strategy(self) -> None:
        template = _create_synthetic_payload(30, 30, circle_center=(15, 15), circle_radius=10)
        strategy = TemplateMatchStrategy(template=template, threshold=0.7)

        frame_match = _create_synthetic_payload(100, 100, circle_center=(40, 40), circle_radius=10)
        res = strategy.analyze(frame_match)
        self.assertTrue(res.found)
        self.assertGreaterEqual(res.confidence, 0.7)


if __name__ == "__main__":
    unittest.main()
