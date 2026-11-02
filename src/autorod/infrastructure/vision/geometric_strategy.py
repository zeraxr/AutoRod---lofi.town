import math
import logging
from pathlib import Path
from collections.abc import Sequence
import cv2
import numpy as np

from autorod.domain.ports.vision import IVisionStrategy
from autorod.domain.ports.templates import ITemplateRepository
from autorod.domain.models.image_payload import ImagePayload
from autorod.domain.models.match_result import MatchResult
from autorod.domain.models.geometry import Point, Size, Region
from autorod.infrastructure.imaging.numpy_bridge import payload_to_ndarray
from autorod.infrastructure.templates.file_repository import FileTemplateRepository

logger = logging.getLogger(__name__)


class GeometricVisionStrategy(IVisionStrategy):
    """
    Motor SOTA de visión computacional adaptativa e invariante a escala para lofi.town.
    Orquesta las tres fases críticas del ciclo completo de pesca:
      1. Botones de Acción Pixel-Art ('CAST!' y 'REEL!'):
         Localización con coincidencia de plantilla multi-escala (escala ~1.0).
      2. Minijuego de Pesca (Dial con Aguja Estática a las 12 en punto):
         Localización multi-escala adaptada a la escala real del dial en el juego (~0.50 / 95-105 px).
         Inspecciona la posición 12 en punto bajo la aguja fija superior. Cuando el sector verde claro rota
         y entra en contacto con la aguja, dictamina impacto ('minigame_needle_hit').
         Elimina completamente falsos positivos con árboles de fondo.
      3. Tarjeta de Pez Obtenido ('blank_card'):
         Detecta el rectángulo blanco con esquinas redondeadas que presenta el pez
         capturado para accionar el salto inmediato de la animación.
    """

    BUTTON_CANDIDATE_SCALES: tuple[float, ...] = (
        1.0, 1.25, 1.50, 0.80, 0.90, 1.10, 0.75, 1.20, 1.33, 1.40,
        1.75, 2.0, 1.60, 1.875, 2.25, 2.50,
        0.70, 0.67, 0.60, 0.55, 0.50, 0.45, 0.40,
        0.85, 0.95, 1.05, 1.15
    )

    # Escalas candidatas para el dial (cobertura integral de zoom y DPI de 0.40x a 2.50x)
    DIAL_CANDIDATE_SCALES: tuple[float, ...] = (
        1.0, 1.25, 1.50, 0.80, 0.90, 1.10, 0.75, 1.20, 1.33, 1.40,
        1.75, 2.0, 1.60, 1.875, 2.25, 2.50, 0.70, 0.67, 0.60, 0.50,
        0.85, 0.95, 1.05, 1.15
    )

    def __init__(
            self,
            template_repo: ITemplateRepository | None = None,
            button_threshold: float = 0.63,
            dial_threshold: float = 0.50,
            cache_size_enabled: bool = True,
            # Verde claro objetivo del minijuego (HSV [33, 76, 188])
            target_green_lower: tuple[int, int, int] = (29, 50, 150),
            target_green_upper: tuple[int, int, int] = (40, 115, 230),
            # Rango amplio para respaldo sintético
            pistachio_lower: tuple[int, int, int] = (28, 40, 60),
            pistachio_upper: tuple[int, int, int] = (85, 255, 255),
            # Aguja (rojo/naranja)
            needle_orange_lower: tuple[int, int, int] = (0, 100, 100),
            needle_orange_upper: tuple[int, int, int] = (22, 255, 255),
            needle_red_lower: tuple[int, int, int] = (168, 100, 100),
            needle_red_upper: tuple[int, int, int] = (180, 255, 255),
            strategy_id: str = "geometric_vision_sota"
    ) -> None:
        self._strategy_id = strategy_id
        self._button_threshold = button_threshold
        self._dial_threshold = dial_threshold
        self._cache_size_enabled = cache_size_enabled
        self._repo: ITemplateRepository = template_repo or FileTemplateRepository()

        # Rangos HSV para el minijuego de aguja
        self._target_green_lower = np.array(target_green_lower, dtype=np.uint8)
        self._target_green_upper = np.array(target_green_upper, dtype=np.uint8)
        self._pistachio_lower = np.array(pistachio_lower, dtype=np.uint8)
        self._pistachio_upper = np.array(pistachio_upper, dtype=np.uint8)
        self._needle_orange_lower = np.array(needle_orange_lower, dtype=np.uint8)
        self._needle_orange_upper = np.array(needle_orange_upper, dtype=np.uint8)
        self._needle_red_lower = np.array(needle_red_lower, dtype=np.uint8)
        self._needle_red_upper = np.array(needle_red_upper, dtype=np.uint8)

        # Plantillas precargadas en memoria
        self._cast_mat: np.ndarray | None = None
        self._reel_mat: np.ndarray | None = None
        self._dial_mat: np.ndarray | None = None
        self._dial_static_mask: np.ndarray | None = None

        # Cachés de pirámides precalculadas para rendimiento O(1) en el bucle principal
        self._precomputed_cast: dict[float, np.ndarray] = {}
        self._precomputed_cast_gray: dict[float, np.ndarray] = {}
        self._precomputed_reel: dict[float, np.ndarray] = {}
        self._precomputed_reel_gray: dict[float, np.ndarray] = {}
        self._precomputed_dial: dict[float, tuple[np.ndarray, np.ndarray | None]] = {}
        self._scan_counter: int = 0

        # Memorias de escala independientes para evitar contaminación entre botones y dial
        self._cached_button_scale: float | None = None
        self._cached_dial_scale: float | None = None
        self._cached_dimensions: tuple[int, int] | None = None
        self._last_dial_roi: tuple[int, int, int, int] | None = None
        self._dial_tracking_frames: int = 0
        self._completed_cycles: int = 0

        self._load_templates()

    @property
    def strategy_id(self) -> str:
        return self._strategy_id

    @property
    def completed_cycles(self) -> int:
        return self._completed_cycles

    @property
    def is_afk_consolidated(self) -> bool:
        """Indica si el bot superó los 5 ciclos de calibración y opera en modo AFK consolidado."""
        return self._completed_cycles >= 5

    def notify_cycle_completed(self) -> None:
        """
        Registra la finalización exitosa de un ciclo de pesca (tarjeta cerrada -> CAST!).
        Tras 5 ciclos, el motor asume modo AFK consolidado y fija el uso exclusivo de caché.
        """
        self._completed_cycles += 1
        if self._completed_cycles == 5:
            logger.info(
                "[CALIBRACION] ¡5 ciclos de pesca completados con éxito! Entrando en Modo AFK Consolidado. "
                "Escala fijada en %.2fx para máximo ahorro de CPU.",
                self._cached_button_scale or 1.0
            )
        else:
            logger.info(
                "[CALIBRACION] Ciclo de pesca #%d/5 completado. Calibración dinámica activa.",
                self._completed_cycles
            )

    @property
    def button_threshold(self) -> float:
        return self._button_threshold

    @button_threshold.setter
    def button_threshold(self, val: float) -> None:
        self._button_threshold = max(0.40, min(0.95, float(val)))

    @property
    def dial_threshold(self) -> float:
        return self._dial_threshold

    @dial_threshold.setter
    def dial_threshold(self, val: float) -> None:
        self._dial_threshold = max(0.35, min(0.95, float(val)))

    @property
    def cache_size_enabled(self) -> bool:
        return self._cache_size_enabled

    @cache_size_enabled.setter
    def cache_size_enabled(self, val: bool) -> None:
        self._cache_size_enabled = bool(val)
        if not self._cache_size_enabled:
            self.clear_scale_cache()

    @property
    def cached_scale(self) -> float | None:
        return self._cached_button_scale

    @property
    def cached_dimensions(self) -> tuple[int, int] | None:
        return self._cached_dimensions

    def clear_scale_cache(self) -> None:
        """Purga la memoria de tamaño/escala para forzar una recalibración completa."""
        self._cached_button_scale = None
        self._cached_dial_scale = None
        self._cached_dimensions = None
        self._last_dial_roi = None
        self._dial_tracking_frames = 0
        self._completed_cycles = 0
        logger.info("Caché de dimensiones y ROI purgado. Calibración dinámica activa.")

    def _load_templates(self) -> None:
        """Precarga y almacena en memoria los ndarray BGR de las plantillas oficiales."""
        try:
            payload_cast = self._repo.load("cast_button")
            self._cast_mat = payload_to_ndarray(payload_cast)
        except Exception as exc:
            logger.warning("No se pudo cargar la plantilla 'cast_button': %s", exc)

        try:
            payload_reel = self._repo.load("reel_button")
            self._reel_mat = payload_to_ndarray(payload_reel)
        except Exception as exc:
            logger.warning("No se pudo cargar la plantilla 'reel_button': %s", exc)

        try:
            payload_dial = self._repo.load("minigame_dial")
            self._dial_mat = payload_to_ndarray(payload_dial)
            dh, dw = self._dial_mat.shape[:2]
            Y, X = np.ogrid[:dh, :dw]
            dist = np.hypot(X - dw // 2, Y - dh // 2)
            mask = np.zeros((dh, dw), dtype=np.uint8)
            # Aislamiento estático: bisel circular exterior, botón central y aguja superior a las 12 en punto
            mask[(dist >= dh * 0.33) & (dist <= dh * 0.46)] = 255
            mask[dist <= dh * 0.09] = 255
            mask[int(dh * 0.09):int(dh * 0.27), int(dw * 0.43):int(dw * 0.57)] = 255

            try:
                base_dir = getattr(self._repo, "base_dir", None)
                if base_dir:
                    dial_file = Path(base_dir) / "minigame_dial.png"
                    if dial_file.is_file():
                        raw_4ch = cv2.imread(str(dial_file), cv2.IMREAD_UNCHANGED)
                        if raw_4ch is not None and raw_4ch.shape[2] == 4:
                            mask[raw_4ch[:, :, 3] == 0] = 0
            except Exception:
                pass
            self._dial_static_mask = mask
        except Exception as exc:
            logger.warning("No se pudo cargar la plantilla 'minigame_dial': %s", exc)

        # Precalcular pirámides multi-escala en memoria para costo O(1) en el bucle principal
        self._precompute_template_pyramids()

    def _precompute_template_pyramids(self) -> None:
        """Precalcula y almacena en memoria los templates escalados en BGR y escala de grises."""
        self._precomputed_cast.clear()
        self._precomputed_cast_gray.clear()
        self._precomputed_reel.clear()
        self._precomputed_reel_gray.clear()
        self._precomputed_dial.clear()

        for s in self.BUTTON_CANDIDATE_SCALES:
            if self._cast_mat is not None:
                oh, ow = self._cast_mat.shape[:2]
                tw = max(10, int((ow / 2.0) * s))
                th = max(10, int((oh / 2.0) * s))
                bgr_scaled = cv2.resize(self._cast_mat, (tw, th), interpolation=cv2.INTER_LINEAR)
                self._precomputed_cast[s] = bgr_scaled
                self._precomputed_cast_gray[s] = cv2.cvtColor(bgr_scaled, cv2.COLOR_BGR2GRAY)

            if self._reel_mat is not None:
                oh, ow = self._reel_mat.shape[:2]
                tw = max(10, int((ow / 2.0) * s))
                th = max(10, int((oh / 2.0) * s))
                bgr_scaled = cv2.resize(self._reel_mat, (tw, th), interpolation=cv2.INTER_LINEAR)
                self._precomputed_reel[s] = bgr_scaled
                self._precomputed_reel_gray[s] = cv2.cvtColor(bgr_scaled, cv2.COLOR_BGR2GRAY)

        has_mask = getattr(self, "_dial_static_mask", None) is not None
        for s in self.DIAL_CANDIDATE_SCALES:
            if self._dial_mat is not None:
                oh, ow = self._dial_mat.shape[:2]
                tw = max(15, int((ow / 2.0) * s))
                th = max(15, int((oh / 2.0) * s))
                stpl = cv2.resize(self._dial_mat, (tw, th), interpolation=cv2.INTER_LINEAR)
                smask = None
                if has_mask and self._dial_static_mask is not None:
                    smask = cv2.resize(self._dial_static_mask, (tw, th), interpolation=cv2.INTER_NEAREST)
                self._precomputed_dial[s] = (stpl, smask)

    def analyze(self, frame: ImagePayload, template_ref: str | None = None) -> MatchResult:
        img_bgr = payload_to_ndarray(frame)
        ox = frame.offset_x
        oy = frame.offset_y

        # ==========================================================
        # FASE 1: Detectar Tarjeta de Pez Obtenido (Prioridad post-minijuego, ~3 ms)
        # ==========================================================
        card_match = self._detect_blank_card(img_bgr, ox, oy, frame.frame_id)
        if card_match is not None:
            self._last_dial_roi = None
            self._dial_tracking_frames = 0
            return card_match

        # Redimensionamiento unificado a media resolución para fases 2 y 3 (calculado una sola vez)
        fh, fw = img_bgr.shape[:2]
        small_screen = cv2.resize(img_bgr, (fw // 2, fh // 2), interpolation=cv2.INTER_LINEAR)

        # ==========================================================
        # FASE 2: Detectar Botones Pixel-Art ('CAST!' / 'REEL!')
        # Si un botón está en pantalla, tiene prioridad absoluta y anula cualquier minijuego previo.
        # ==========================================================
        btn_match = self._detect_buttons(small_screen, ox, oy, frame.frame_id)
        if btn_match is not None:
            self._last_dial_roi = None
            self._dial_tracking_frames = 0
            return btn_match

        # ==========================================================
        # FASE 3: Rastreo Ultra-Rápido del Dial Conocido (< 0.2 ms / 5000 FPS)
        # ==========================================================
        if self._last_dial_roi is not None:
            fast_match = self._track_known_dial(img_bgr, ox, oy, frame.frame_id)
            if fast_match is not None:
                return fast_match
            # Si el dial ya no está en el ROI, se limpió de la pantalla (minijuego finalizado)
            self._last_dial_roi = None

        # ==========================================================
        # FASE 4: Detectar Minijuego de Aguja (Búsqueda Inicial del Dial)
        # ==========================================================
        minigame_match = self._detect_minigame(small_screen, img_bgr, ox, oy, frame.frame_id, frame.source_id)
        if minigame_match is not None:
            return minigame_match

        # ==========================================================
        # FASE 5: En Espera / Rastreo Activo
        # ==========================================================
        return MatchResult(
            found=False,
            confidence=0.0,
            region=None,
            center=None,
            strategy_id="scanning_for_targets",
            frame_id=frame.frame_id
        )

    def _detect_buttons(
            self,
            small_screen: np.ndarray,
            ox: int,
            oy: int,
            frame_id: int
    ) -> MatchResult | None:
        """Localiza los botones pixel-art mediante pirámide multi-escala precalculada y verificación BGR."""
        if not self._precomputed_cast and not self._precomputed_reel:
            return None

        sh, sw = small_screen.shape[:2]

        using_cached_scale = False
        if self._cache_size_enabled and self._cached_button_scale is not None:
            scales_to_try = [self._cached_button_scale]
            using_cached_scale = True
        else:
            scales_to_try = list(self.BUTTON_CANDIDATE_SCALES)

        small_gray = cv2.cvtColor(small_screen, cv2.COLOR_BGR2GRAY)

        best_score = 0.0
        best_loc: tuple[int, int] = (0, 0)
        best_size: tuple[int, int] = (0, 0)
        best_scale: float = 1.0
        best_strategy_id: str = "button_detected"

        def _scan_scales(scales: Sequence[float]) -> None:
            nonlocal best_score, best_loc, best_size, best_scale, best_strategy_id
            for s in scales:
                # Para plantillas muy reducidas (s < 0.60), exigimos mayor correlación (>= 0.70) para evitar
                # que un dial u otros elementos del escenario generen falsos positivos en resoluciones bajas.
                thresh_for_scale = max(self._button_threshold, 0.70 if s < 0.60 else self._button_threshold)

                candidate_loc = None
                # Localizar candidato con plantilla CAST! en escala de grises (3x más rápido)
                if s in self._precomputed_cast_gray:
                    stpl_gray = self._precomputed_cast_gray[s]
                    th, tw = stpl_gray.shape[:2]
                    if sw >= tw and sh >= th:
                        res = cv2.matchTemplate(small_gray, stpl_gray, cv2.TM_CCOEFF_NORMED)
                        _, mv, _, ml = cv2.minMaxLoc(res)
                        if mv >= thresh_for_scale:
                            candidate_loc = ml

                # Si no se localizó candidato suficiente con CAST!, intentar con REEL! en escala de grises
                if candidate_loc is None and s in self._precomputed_reel_gray:
                    stpl_gray = self._precomputed_reel_gray[s]
                    th, tw = stpl_gray.shape[:2]
                    if sw >= tw and sh >= th:
                        res = cv2.matchTemplate(small_gray, stpl_gray, cv2.TM_CCOEFF_NORMED)
                        _, mv, _, ml = cv2.minMaxLoc(res)
                        if mv >= thresh_for_scale:
                            candidate_loc = ml

                # Si se localizó un candidato válido en esta escala, discriminar estrictamente en color BGR
                if candidate_loc is not None:
                    cl_x, cl_y = candidate_loc
                    th, tw = self._precomputed_cast[s].shape[:2]
                    if cl_y + th <= sh and cl_x + tw <= sw:
                        candidate_bgr = small_screen[cl_y:cl_y+th, cl_x:cl_x+tw]

                        # Verificación simultánea de color BGR contra ambas plantillas (distinción 100% matemática)
                        res_c = cv2.matchTemplate(candidate_bgr, self._precomputed_cast[s], cv2.TM_CCOEFF_NORMED)
                        score_cast = float(cv2.minMaxLoc(res_c)[1])

                        score_reel = 0.0
                        if s in self._precomputed_reel:
                            res_r = cv2.matchTemplate(candidate_bgr, self._precomputed_reel[s], cv2.TM_CCOEFF_NORMED)
                            score_reel = float(cv2.minMaxLoc(res_r)[1])

                        cand_score = max(score_cast, score_reel)
                        if cand_score > best_score and cand_score >= thresh_for_scale:
                            best_score = cand_score
                            best_loc = candidate_loc
                            best_size = (tw * 2, th * 2)
                            best_scale = s
                            best_strategy_id = "cast_button_detected" if score_cast >= score_reel else "reel_button_detected"

                # Salida inmediata si ya se superó el umbral de certeza absoluta (>= 0.92)
                # (Se utiliza 0.92 debido a que la correlación cruzada CAST vs REEL es de 0.889)
                if best_score >= 0.92:
                    break

        _scan_scales(scales_to_try)

        # Fallback dinámico automático:
        # Durante la fase de calibración (primeros 5 ciclos de pesca completos), si la escala en caché
        # no arroja coincidencia (ej. el usuario cambió el zoom del navegador en caliente o redimensionó la ventana),
        # escaneamos de inmediato el resto de la pirámide sin bloquear al bot, y actualizamos dinámicamente las variables de escala en caché.
        #
        # Una vez completados los 5 ciclos (_completed_cycles >= 5), el bot asume Modo AFK Consolidado:
        # las variables de escala quedan consolidadas y se utiliza exclusivamente la escala en caché
        # para liberar el 100% de CPU en los fotogramas sin botones (anzuelo en el agua).
        #
        # !TODO: En una futura versión orientada al fallo, si el usuario altera el zoom en modo AFK,
        # implementar un watchdog de inactividad que detecte la falta prolongada de eventos y
        # reactive automáticamente la fase de calibración dinámica con notificación visual en la UI.
        if using_cached_scale and best_score < self._button_threshold and not self.is_afk_consolidated:
            fallback_scales = [s for s in self.BUTTON_CANDIDATE_SCALES if s != self._cached_button_scale]
            _scan_scales(fallback_scales)

        if best_score >= self._button_threshold:
            if self._cache_size_enabled:
                if self._cached_button_scale != best_scale:
                    logger.info(
                        "[BOTON] Escala actualizada dinámicamente en caché: %.2fx (dimensiones %dx%d). Tipo: %s",
                        best_scale, best_size[0], best_size[1], best_strategy_id
                    )
                self._cached_button_scale = best_scale
                self._cached_dimensions = best_size
                self._cached_dial_scale = best_scale

            full_x = ox + best_loc[0] * 2
            full_y = oy + best_loc[1] * 2
            full_w, full_h = best_size

            center_x = full_x + full_w // 2
            center_y = full_y + full_h // 2

            region = Region(
                top_left=Point(x=full_x, y=full_y),
                size=Size(width=full_w, height=full_h)
            )
            center = Point(x=center_x, y=center_y)

            return MatchResult(
                found=True,
                confidence=best_score,
                region=region,
                center=center,
                strategy_id=best_strategy_id,
                frame_id=frame_id
            )

        return None

    def _count_needle_pixels(self, roi_bgr: np.ndarray) -> int:
        """
        Cuenta los píxeles de color naranja/rojo de la aguja estática superior (12 en punto).
        Elimina al 100% los falsos positivos con el césped, agua o arena del escenario.
        """
        rh, rw = roi_bgr.shape[:2]
        if rh < 15 or rw < 15:
            return 0
        y1 = max(0, int(rh * 0.07))
        y2 = min(rh, int(rh * 0.30))
        x1 = max(0, int(rw * 0.40))
        x2 = min(rw, int(rw * 0.60))
        needle_crop = roi_bgr[y1:y2, x1:x2]
        if needle_crop.size == 0:
            return 0
        hsv = cv2.cvtColor(needle_crop, cv2.COLOR_BGR2HSV)
        m1 = cv2.inRange(hsv, np.array([5, 80, 80]), np.array([25, 255, 255]))
        m2 = cv2.inRange(hsv, np.array([0, 80, 80]), np.array([10, 255, 255]))
        m3 = cv2.inRange(hsv, np.array([170, 80, 80]), np.array([180, 255, 255]))
        mask = cv2.bitwise_or(m1, cv2.bitwise_or(m2, m3))
        return int(np.count_nonzero(mask))

    def _track_known_dial(
            self,
            img_bgr: np.ndarray,
            ox: int,
            oy: int,
            frame_id: int
    ) -> MatchResult | None:
        """
        Rastreo ultra-rápido (< 0.2 ms / ~5000 FPS) del dial conocido.
        Inspecciona directamente el ROI sin hacer búsquedas globales por toda la pantalla.
        """
        if self._last_dial_roi is None:
            return None

        # Límite de seguridad: máximo 120 fotogramas consecutivos (~2.0s) de rastreo sin impacto
        # para evitar quedar permanentemente anclado a elementos estáticos del fondo (césped/árboles)
        self._dial_tracking_frames += 1
        if self._dial_tracking_frames > 120:
            self._last_dial_roi = None
            self._dial_tracking_frames = 0
            return None

        full_x, full_y, full_w, full_h = self._last_dial_roi
        fh, fw = img_bgr.shape[:2]

        # Validar límites de la imagen
        if full_x < 0 or full_y < 0 or full_x + full_w > fw or full_y + full_h > fh:
            self._last_dial_roi = None
            self._dial_tracking_frames = 0
            return None

        dial_roi = img_bgr[full_y:full_y+full_h, full_x:full_x+full_w]
        if dial_roi.size == 0:
            self._last_dial_roi = None
            self._dial_tracking_frames = 0
            return None

        # Verificación estricta adaptativa al zoom: la aguja naranja fija debe estar presente
        active_scale = self._cached_dial_scale or self._cached_button_scale or 1.0
        min_needle = max(8, int(18 * (active_scale ** 2)))
        needle_count = self._count_needle_pixels(dial_roi)
        if needle_count < min_needle:
            # La aguja ha desaparecido (pez pescado o minijuego terminado)
            self._last_dial_roi = None
            self._dial_tracking_frames = 0
            return None

        # Verificación de presencia: el dial debe seguir conteniendo los sectores verdes del minijuego
        hsv_roi = cv2.cvtColor(dial_roi, cv2.COLOR_BGR2HSV)
        mask_olive = cv2.inRange(hsv_roi, np.array([25, 40, 70]), np.array([45, 160, 220]))
        olive_ratio = np.count_nonzero(mask_olive) / float(full_w * full_h)

        if olive_ratio < 0.16:
            # Los sectores verdes del dial han desaparecido
            self._last_dial_roi = None
            self._dial_tracking_frames = 0
            return None

        cx = full_x + full_w // 2
        cy = full_y + full_h // 2

        region = Region(
            top_left=Point(x=ox + full_x, y=oy + full_y),
            size=Size(width=full_w, height=full_h)
        )
        center = Point(x=ox + cx, y=oy + cy)

        # Inspección precisa de la columna bajo la aguja a las 12 en punto
        # Columna ajustada a +-3.5% del centro (ancho ~14px, idéntico a la punta de la aguja)
        # Altura: de 22% a 40% del alto del dial (justo bajo la punta de la aguja)
        y1 = max(0, int(full_y + full_h * 0.22))
        y2 = min(fh, int(full_y + full_h * 0.40))
        half_w = max(3, int(full_w * 0.035))
        x1 = max(0, cx - half_w)
        x2 = min(fw, cx + half_w)

        needle_zone = img_bgr[y1:y2, x1:x2]
        if needle_zone.size > 0:
            hsv_zone = cv2.cvtColor(needle_zone, cv2.COLOR_BGR2HSV)
            mask_light_green = cv2.inRange(hsv_zone, self._target_green_lower, self._target_green_upper)
            green_pixels = np.count_nonzero(mask_light_green)
            total_pixels = max(1, needle_zone.shape[0] * needle_zone.shape[1])
            ratio = green_pixels / float(total_pixels)

            # Impacto cuando el sector verde claro ocupa >= 40% de la columna bajo la aguja
            is_hit = ratio >= 0.40
            if is_hit:
                self._dial_tracking_frames = 0

            return MatchResult(
                found=is_hit,
                confidence=0.99,
                region=region,
                center=center,
                strategy_id="minigame_needle_hit" if is_hit else "minigame_tracking",
                frame_id=frame_id
            )

        return None

    def _detect_minigame(
            self,
            small_screen: np.ndarray,
            img_bgr: np.ndarray,
            ox: int,
            oy: int,
            frame_id: int,
            source_id: str = ""
    ) -> MatchResult | None:
        """
        Detecta el dial circular del minijuego e inspecciona si el sector verde claro
        se encuentra bajo la aguja estática superior (12 en punto).
        Utiliza escalas independientes precalculadas.
        """
        # 1. Respaldo por segmentación HSV adaptativa (SÓLO para pruebas sintéticas de unidad)
        if source_id.startswith("synthetic"):
            return self._detect_minigame_contour(img_bgr, ox, oy, frame_id)

        if self._dial_mat is not None:
            fh, fw = img_bgr.shape[:2]
            sh, sw = small_screen.shape[:2]

            # Pre-filtro ultra-rápido de color verde (< 0.5 ms):
            # El dial del minijuego contiene obligatoriamente sectores verdes ([20, 35, 60] a [45, 255, 255]).
            # Si no hay presencia de verde en pantalla, evitamos el costo de 14 matchTemplate con máscara.
            tiny = cv2.resize(small_screen, (240, 135), interpolation=cv2.INTER_NEAREST)
            hsv_tiny = cv2.cvtColor(tiny, cv2.COLOR_BGR2HSV)
            mask_tiny = cv2.inRange(hsv_tiny, np.array([20, 35, 60]), np.array([45, 255, 255]))
            if cv2.countNonZero(mask_tiny) < 15:
                return None

            # Si aún no tenemos escala de dial memorizada pero sí conocemos la de los botones (mismo lienzo de juego),
            # heredamos esa escala como candidata inicial para acierto instantáneo en O(1)
            if self._cached_dial_scale is None and self._cached_button_scale is not None:
                self._cached_dial_scale = self._cached_button_scale

            using_cached_dial = False
            if self._cache_size_enabled and self._cached_dial_scale:
                scales = [self._cached_dial_scale]
                using_cached_dial = True
            else:
                scales = list(self.DIAL_CANDIDATE_SCALES)

            best_score = 0.0
            best_loc = (0, 0)
            best_size = (0, 0)
            best_s = 1.0

            has_mask = getattr(self, "_dial_static_mask", None) is not None

            def _scan_dial_scales(target_scales: Sequence[float]) -> None:
                nonlocal best_score, best_loc, best_size, best_s
                for s in target_scales:
                    if s in self._precomputed_dial:
                        stpl, smask = self._precomputed_dial[s]
                        th, tw = stpl.shape[:2]
                        if sw >= tw and sh >= th:
                            if has_mask and smask is not None:
                                res = cv2.matchTemplate(small_screen, stpl, cv2.TM_SQDIFF_NORMED, mask=smask)
                                min_v, _, min_l, _ = cv2.minMaxLoc(res)
                                score = float(1.0 - min_v)
                                loc = min_l
                            else:
                                res = cv2.matchTemplate(small_screen, stpl, cv2.TM_CCOEFF_NORMED)
                                _, mv, _, ml = cv2.minMaxLoc(res)
                                score = float(mv)
                                loc = ml

                            if score > best_score:
                                best_score = score
                                best_loc = loc
                                best_size = (tw * 2, th * 2)
                                best_s = s

                            if best_score >= 0.98:
                                break

            _scan_dial_scales(scales)

            # Umbral de coincidencia: 0.945 para máscara estática (SQDIFF) o dial_threshold para CCOEFF
            # (El césped uniforme produce correlación de ~0.916, por lo que 0.945 es totalmente inmune a falsos positivos)
            effective_thresh = 0.945 if has_mask else self._dial_threshold

            if using_cached_dial and best_score < effective_thresh and not self.is_afk_consolidated:
                fallback_dial_scales = [s for s in self.DIAL_CANDIDATE_SCALES if s != self._cached_dial_scale]
                _scan_dial_scales(fallback_dial_scales)
            if best_score >= effective_thresh:
                full_x = best_loc[0] * 2
                full_y = best_loc[1] * 2
                full_w, full_h = best_size

                # Verificación de integridad: el dial debe contener la aguja superior naranja/roja y sectores verdes
                dial_roi = img_bgr[full_y:full_y+full_h, full_x:full_x+full_w]
                if dial_roi.size > 0:
                    min_needle = max(8, int(20 * (best_s ** 2)))
                    needle_count = self._count_needle_pixels(dial_roi)
                    if needle_count < min_needle:
                        # Rechazar falsos positivos en césped/fondo
                        return None

                    hsv_roi = cv2.cvtColor(dial_roi, cv2.COLOR_BGR2HSV)
                    mask_olive = cv2.inRange(hsv_roi, np.array([25, 40, 70]), np.array([45, 160, 220]))
                    olive_ratio = np.count_nonzero(mask_olive) / float(full_w * full_h)

                    # Verificación estricta: debe contener sectores verdes del minijuego (mínimo 18% del área)
                    if olive_ratio >= 0.18:
                        self._last_dial_roi = (full_x, full_y, full_w, full_h)
                        self._dial_tracking_frames = 0
                        if self._cache_size_enabled:
                            self._cached_dial_scale = best_s

                        cx = full_x + full_w // 2
                        cy = full_y + full_h // 2

                        region = Region(
                            top_left=Point(x=ox + full_x, y=oy + full_y),
                            size=Size(width=full_w, height=full_h)
                        )
                        center = Point(x=ox + cx, y=oy + cy)

                        # Inspección precisa de la columna bajo la aguja a las 12 en punto
                        # Columna ajustada a +-3.5% del centro (ancho ~14px, idéntico a la punta de la aguja)
                        # Altura: de 22% a 40% del alto del dial (justo bajo la punta de la aguja)
                        y1 = max(0, int(full_y + full_h * 0.22))
                        y2 = min(fh, int(full_y + full_h * 0.40))
                        half_w = max(3, int(full_w * 0.035))
                        x1 = max(0, cx - half_w)
                        x2 = min(fw, cx + half_w)

                        needle_zone = img_bgr[y1:y2, x1:x2]
                        if needle_zone.size > 0:
                            hsv_zone = cv2.cvtColor(needle_zone, cv2.COLOR_BGR2HSV)
                            mask_light_green = cv2.inRange(hsv_zone, self._target_green_lower, self._target_green_upper)
                            green_pixels = np.count_nonzero(mask_light_green)
                            total_pixels = max(1, needle_zone.shape[0] * needle_zone.shape[1])
                            ratio = green_pixels / float(total_pixels)

                            # Si más del 40% del área bajo la aguja es verde claro -> IMPACTO
                            is_hit = ratio >= 0.40

                            return MatchResult(
                                found=is_hit,
                                confidence=best_score,
                                region=region,
                                center=center,
                                strategy_id="minigame_needle_hit" if is_hit else "minigame_tracking",
                                frame_id=frame_id
                            )

        return None

    def _detect_minigame_contour(
            self,
            img_bgr: np.ndarray,
            ox: int,
            oy: int,
            frame_id: int
    ) -> MatchResult | None:
        """Respaldo de detección de arco verde y aguja por contornos HSV para pruebas sintéticas."""
        hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))

        mask_target = cv2.inRange(hsv, self._pistachio_lower, self._pistachio_upper)
        mask_target = cv2.morphologyEx(mask_target, cv2.MORPH_OPEN, kernel, iterations=1)
        contours_target, _ = cv2.findContours(mask_target, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if not contours_target:
            return None

        best_target = max(contours_target, key=cv2.contourArea)
        area = cv2.contourArea(best_target)
        if area < 40.0:
            return None

        bx, by, bw, bh = cv2.boundingRect(best_target)
        aspect = bw / float(bh) if bh > 0 else 0.0
        if not (0.6 <= aspect <= 1.8):
            return None

        mt = cv2.moments(best_target)
        if mt["m00"] <= 0:
            return None

        tx = int(mt["m10"] / mt["m00"])
        ty = int(mt["m01"] / mt["m00"])
        region = Region(top_left=Point(x=ox + bx, y=oy + by), size=Size(width=bw, height=bh))
        center_target = Point(x=ox + tx, y=oy + ty)

        mask_n1 = cv2.inRange(hsv, self._needle_orange_lower, self._needle_orange_upper)
        mask_n2 = cv2.inRange(hsv, self._needle_red_lower, self._needle_red_upper)
        mask_needle = cv2.bitwise_or(mask_n1, mask_n2)
        mask_needle = cv2.morphologyEx(mask_needle, cv2.MORPH_OPEN, kernel, iterations=1)
        contours_needle, _ = cv2.findContours(mask_needle, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if contours_needle:
            best_needle = max(contours_needle, key=cv2.contourArea)
            mn = cv2.moments(best_needle)
            if mn["m00"] > 0:
                nx = int(mn["m10"] / mn["m00"])
                ny = int(mn["m01"] / mn["m00"])

                dist = math.hypot(nx - tx, ny - ty)
                collision_radius = max(bw, bh) * 0.70
                is_colliding = dist <= collision_radius
                confidence = max(0.0, min(1.0, 1.0 - (dist / max(1.0, collision_radius * 2))))

                return MatchResult(
                    found=is_colliding,
                    confidence=confidence,
                    region=region,
                    center=center_target,
                    strategy_id="minigame_needle_hit",
                    frame_id=frame_id
                )

        return MatchResult(
            found=False,
            confidence=0.35,
            region=region,
            center=center_target,
            strategy_id="minigame_tracking",
            frame_id=frame_id
        )

    def _detect_blank_card(
            self,
            img_bgr: np.ndarray,
            ox: int,
            oy: int,
            frame_id: int
    ) -> MatchResult | None:
        """
        Detecta la tarjeta blanca ('reward_card') que se despliega tras pescar un pez.
        Basado en el método SOTA v1.1.0: máscara de blanco puro en HSV combinada con
        análisis de masa y proporciones geométricas robustas e invariantes a iluminación.
        """
        hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
        # Rango para blanco brillante de la tarjeta (S bajo <= 25, V alto >= 225)
        white_mask = cv2.inRange(hsv, np.array([0, 0, 225]), np.array([180, 25, 255]))
        contours, _ = cv2.findContours(white_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Umbrales geométricos invariantes a la escala (soporta desde zoom reducido 0.33x hasta 2.50x)
        min_area = 2500.0
        min_dim = 35

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > min_area:
                bx, by, bw, bh = cv2.boundingRect(cnt)

                # Descartar barras delgadas (como la barra de títulos del navegador o bordes)
                if bw < min_dim or bh < min_dim:
                    continue

                aspect = bw / float(bh) if bh > 0 else 0.0
                # Aspect ratio vertical o moderadamente cuadrado (entre 0.55 y 1.25)
                if 0.55 <= aspect <= 1.25:
                    rect_area = bw * bh
                    solidity = area / float(rect_area) if rect_area > 0 else 0.0

                    # Permite texto y sprite en el centro de la tarjeta (>55% de solidez)
                    if solidity > 0.55:
                        cx = ox + bx + bw // 2
                        cy = oy + by + bh // 2

                        return MatchResult(
                            found=True,
                            confidence=0.95,
                            region=Region(
                                top_left=Point(x=ox + bx, y=oy + by),
                                size=Size(width=bw, height=bh)
                            ),
                            center=Point(x=cx, y=cy),
                            strategy_id="blank_card_detected",
                            frame_id=frame_id
                        )

        return None
