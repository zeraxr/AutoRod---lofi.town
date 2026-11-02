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

    def test_geometric_strategy_detects_high_zoom_buttons(self) -> None:
        """Verifica que el motor detecte botones en niveles altos de zoom (1.75x y 2.0x)."""
        strategy = GeometricVisionStrategy(template_repo=self.repo)
        tpl_cast = payload_to_ndarray(self.repo.load("cast_button"))

        for zoom in (1.75, 2.0):
            scaled = cv2.resize(tpl_cast, (int(tpl_cast.shape[1] * zoom), int(tpl_cast.shape[0] * zoom)), interpolation=cv2.INTER_LINEAR)
            th, tw = scaled.shape[:2]
            screen = np.full((1080, 1920, 3), 45, dtype=np.uint8)
            screen[300:300+th, 400:400+tw] = scaled

            payload = ImagePayload(
                width=1920,
                height=1080,
                pixel_format=PixelFormat.BGR8,
                stride=1920 * 3,
                data=screen.tobytes(),
                frame_id=30,
                captured_at_ns=0,
                source_id=f"zoom_{zoom}"
            )
            strategy.clear_scale_cache()
            res = strategy.analyze(payload)
            self.assertTrue(res.found, f"Fallo al detectar botón a zoom {zoom}x")
            self.assertGreaterEqual(res.confidence, 0.85)

    def test_geometric_strategy_auto_recovers_when_zoom_changes_without_manual_cache_purge(self) -> None:
        """Verifica que si el usuario cambia el zoom en caliente, el motor se auto-recalibre sin requerir purga manual."""
        strategy = GeometricVisionStrategy(template_repo=self.repo, cache_size_enabled=True)
        tpl_cast = payload_to_ndarray(self.repo.load("cast_button"))
        th, tw = tpl_cast.shape[:2]

        # 1. Pantalla a escala normal 1.0x
        screen1 = np.full((1080, 1920, 3), 45, dtype=np.uint8)
        screen1[300:300+th, 400:400+tw] = tpl_cast
        p1 = ImagePayload(width=1920, height=1080, pixel_format=PixelFormat.BGR8,
                          stride=1920*3, data=screen1.tobytes(), frame_id=31,
                          captured_at_ns=0, source_id="s1")
        res1 = strategy.analyze(p1)
        self.assertTrue(res1.found)
        self.assertEqual(strategy.cached_scale, 1.0)

        # 2. El usuario cambia el zoom a 1.50x
        scaled = cv2.resize(tpl_cast, (int(tw * 1.5), int(th * 1.5)), interpolation=cv2.INTER_LINEAR)
        sth, stw = scaled.shape[:2]
        screen2 = np.full((1080, 1920, 3), 45, dtype=np.uint8)
        screen2[300:300+sth, 400:400+stw] = scaled
        p2 = ImagePayload(width=1920, height=1080, pixel_format=PixelFormat.BGR8,
                          stride=1920*3, data=screen2.tobytes(), frame_id=32,
                          captured_at_ns=0, source_id="s2")

        # Sin llamar a clear_scale_cache(), analyze() debe auto-recuperarse y actualizar la escala a 1.5
        res2 = strategy.analyze(p2)
        self.assertTrue(res2.found, "El motor no se auto-recuperó al cambiar el zoom")
        self.assertEqual(strategy.cached_scale, 1.5)

    def test_geometric_strategy_preserves_scale_cache_during_fishing_wait_intervals(self) -> None:
        """Verifica que el caché de escala no se borre mientras el anzuelo flota en el agua sin botones."""
        strategy = GeometricVisionStrategy(template_repo=self.repo, cache_size_enabled=True)
        tpl_cast = payload_to_ndarray(self.repo.load("cast_button"))
        tpl_reel = payload_to_ndarray(self.repo.load("reel_button"))
        th, tw = tpl_cast.shape[:2]

        # 1. Detectar CAST! a escala 1.25x
        scaled_cast = cv2.resize(tpl_cast, (int(tw * 1.25), int(th * 1.25)), interpolation=cv2.INTER_LINEAR)
        cth, ctw = scaled_cast.shape[:2]
        screen_cast = np.full((1080, 1920, 3), 45, dtype=np.uint8)
        screen_cast[300:300+cth, 400:400+ctw] = scaled_cast
        p_cast = ImagePayload(width=1920, height=1080, pixel_format=PixelFormat.BGR8,
                              stride=1920*3, data=screen_cast.tobytes(), frame_id=40,
                              captured_at_ns=0, source_id="cast")
        res_cast = strategy.analyze(p_cast)
        self.assertTrue(res_cast.found)
        self.assertEqual(strategy.cached_scale, 1.25)

        # 2. Simular fotogramas de espera mientras el pez pica (sin botón alguno en pantalla)
        blank_screen = np.full((1080, 1920, 3), 45, dtype=np.uint8)
        p_blank = ImagePayload(width=1920, height=1080, pixel_format=PixelFormat.BGR8,
                               stride=1920*3, data=blank_screen.tobytes(), frame_id=41,
                               captured_at_ns=0, source_id="waiting_bite")
        for i in range(5):
            res_blank = strategy.analyze(p_blank)
            self.assertFalse(res_blank.found)

        # El caché de escala DEBE permanecer intacto en 1.25 (NO borrarse durante la espera)
        self.assertEqual(strategy.cached_scale, 1.25)

        # 3. El pez pica y aparece REEL! a la misma escala: debe detectarse de inmediato usando el caché
        scaled_reel = cv2.resize(tpl_reel, (int(tw * 1.25), int(th * 1.25)), interpolation=cv2.INTER_LINEAR)
        rth, rtw = scaled_reel.shape[:2]
        screen_reel = np.full((1080, 1920, 3), 45, dtype=np.uint8)
        screen_reel[300:300+rth, 400:400+rtw] = scaled_reel
        p_reel = ImagePayload(width=1920, height=1080, pixel_format=PixelFormat.BGR8,
                              stride=1920*3, data=screen_reel.tobytes(), frame_id=42,
                              captured_at_ns=0, source_id="reel")
        res_reel = strategy.analyze(p_reel)
        self.assertTrue(res_reel.found)
        self.assertEqual(res_reel.strategy_id, "reel_button_detected")
        self.assertEqual(strategy.cached_scale, 1.25)

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

    def test_button_type_discrimination_between_cast_and_reel(self) -> None:
        """Verifica que el motor distinga con certeza matemática absoluta entre 'CAST!' y 'REEL!'."""
        strategy = GeometricVisionStrategy()
        tpl_cast = payload_to_ndarray(strategy._repo.load("cast_button"))
        tpl_reel = payload_to_ndarray(strategy._repo.load("reel_button"))
        ch, cw = tpl_cast.shape[:2]

        # 1. Probar lienzo con botón CAST!
        canvas_cast = np.full((720, 1280, 3), 40, dtype=np.uint8)
        canvas_cast[200:200+ch, 500:500+cw] = tpl_cast
        p_cast = ImagePayload(width=1280, height=720, pixel_format=PixelFormat.BGR8,
                              stride=1280*3, data=canvas_cast.tobytes(), frame_id=1,
                              captured_at_ns=0, source_id="test_cast")
        res_cast = strategy.analyze(p_cast)
        self.assertTrue(res_cast.found)
        self.assertEqual(res_cast.strategy_id, "cast_button_detected")
        self.assertGreaterEqual(res_cast.confidence, 0.95)

        # 2. Probar lienzo con botón REEL!
        canvas_reel = np.full((720, 1280, 3), 40, dtype=np.uint8)
        canvas_reel[200:200+ch, 500:500+cw] = tpl_reel
        p_reel = ImagePayload(width=1280, height=720, pixel_format=PixelFormat.BGR8,
                              stride=1280*3, data=canvas_reel.tobytes(), frame_id=2,
                              captured_at_ns=0, source_id="test_reel")
        res_reel = strategy.analyze(p_reel)
        self.assertTrue(res_reel.found)
        self.assertEqual(res_reel.strategy_id, "reel_button_detected")
        self.assertGreaterEqual(res_reel.confidence, 0.95)

    def test_five_cycle_calibration_and_afk_consolidation(self) -> None:
        """Verifica la fase de 5 ciclos de calibración dinámica y el paso a Modo AFK Consolidado."""
        strategy = GeometricVisionStrategy()
        self.assertEqual(strategy.completed_cycles, 0)
        self.assertFalse(strategy.is_afk_consolidated)

        # Simular 4 ciclos completados: sigue en calibración dinámica
        for i in range(4):
            strategy.notify_cycle_completed()
            self.assertEqual(strategy.completed_cycles, i + 1)
            self.assertFalse(strategy.is_afk_consolidated)

        # 5to ciclo completado: entra a Modo AFK Consolidado
        strategy.notify_cycle_completed()
        self.assertEqual(strategy.completed_cycles, 5)
        self.assertTrue(strategy.is_afk_consolidated)

        # Purgar el caché restablece el contador de calibración a 0
        strategy.clear_scale_cache()
        self.assertEqual(strategy.completed_cycles, 0)
        self.assertFalse(strategy.is_afk_consolidated)


if __name__ == "__main__":
    unittest.main()
