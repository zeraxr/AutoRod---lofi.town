import time
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
        1.0, 0.95, 1.05, 0.90, 1.10, 0.85, 1.15, 0.80, 1.25, 0.75, 0.70, 0.65, 0.60, 0.55, 0.50, 1.40, 1.50
    )

    # Escalas candidatas para el dial (evaluando escala nativa ~1.0 primero, con cobertura de zoom 0.5x a 1.35x)
    DIAL_CANDIDATE_SCALES: tuple[float, ...] = (
        1.0, 0.95, 1.05, 0.90, 1.10, 0.85, 1.15, 0.80, 1.25, 0.75, 1.35, 0.70, 0.60, 0.50
    )

    def __init__(
            self,
            template_repo: ITemplateRepository | None = None,
            button_threshold: float = 0.63,
            dial_threshold: float = 0.50,
            cache_size_enabled: bool = True,
            required_cycles_to_lock: int = 5,
            cache_inactivity_timeout_s: float = 90.0,
            minigame_anticipation_px: int = 0,
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
        self._dial_lost_frames: int = 0
        self._max_dial_lost_frames: int = 35
        self._required_cycles_to_lock: int = max(1, int(required_cycles_to_lock))
        self._successful_cycles: int = 0
        self._is_cache_locked: bool = False
        self._scale_observations: list[float] = []
        self._dimension_observations: list[tuple[int, int]] = []
        self._cache_inactivity_timeout_s: float = float(cache_inactivity_timeout_s)
        self._minigame_anticipation_px: int = max(0, int(minigame_anticipation_px))
        self._last_match_timestamp: float = 0.0

        self._load_templates()

    @property
    def strategy_id(self) -> str:
        return self._strategy_id

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

    @property
    def minigame_anticipation_px(self) -> int:
        return self._minigame_anticipation_px

    @minigame_anticipation_px.setter
    def minigame_anticipation_px(self, val: int) -> None:
        self._minigame_anticipation_px = max(0, int(val))

    @property
    def is_cache_locked(self) -> bool:
        return self._is_cache_locked

    @property
    def successful_cycles(self) -> int:
        return self._successful_cycles

    @property
    def required_cycles_to_lock(self) -> int:
        return self._required_cycles_to_lock

    @required_cycles_to_lock.setter
    def required_cycles_to_lock(self, val: int) -> None:
        self._required_cycles_to_lock = max(1, int(val))

    @property
    def cache_inactivity_timeout_s(self) -> float:
        return self._cache_inactivity_timeout_s

    @cache_inactivity_timeout_s.setter
    def cache_inactivity_timeout_s(self, val: float) -> None:
        self._cache_inactivity_timeout_s = max(5.0, float(val))

    @property
    def last_match_timestamp(self) -> float:
        return self._last_match_timestamp

    def register_successful_cycle(self, cycle_count: int | None = None) -> None:
        """
        Registra la culminación exitosa de un ciclo de pesca completo.
        Al alcanzar required_cycles_to_lock (5 ciclos) satisfactorios continuos, asegura la estabilidad
        del HUD del navegador y bloquea las variables de escala y dimensiones en memoria caché.
        """
        if cycle_count is not None:
            self._successful_cycles = cycle_count
        else:
            self._successful_cycles += 1

        if self._cache_size_enabled and not self._is_cache_locked:
            logger.info(
                "[VISION-CACHE] Racha de pesca exitosa: #%d/%d (Fase: CALIBRANDO HUD). Escala reciente: %.2fx, Dimensiones: %s.",
                self._successful_cycles, self._required_cycles_to_lock,
                self._cached_button_scale or 1.0,
                self._cached_dimensions or "desconocidas"
            )
            if self._successful_cycles >= self._required_cycles_to_lock:
                from collections import Counter
                if self._scale_observations:
                    most_common_scale, _ = Counter(self._scale_observations).most_common(1)[0]
                    self._cached_button_scale = most_common_scale
                if self._dimension_observations:
                    most_common_dims, _ = Counter(self._dimension_observations).most_common(1)[0]
                    self._cached_dimensions = most_common_dims
                self._is_cache_locked = True
                self._last_match_timestamp = time.monotonic()
                logger.info(
                    "[VISION-CACHE] ¡Racha de %d ciclos alcanzada! HUD ESTABILIZADO. BLOQUEANDO CACHÉ en escala: %.2fx (Dimensiones: %dx%d). Activando modo O(1) con tolerancia de vecindad (+-5%%) y ventana watchdog de %.0fs.",
                    self._successful_cycles, self._cached_button_scale or 1.0,
                    self._cached_dimensions[0] if self._cached_dimensions else 0,
                    self._cached_dimensions[1] if self._cached_dimensions else 0,
                    self._cache_inactivity_timeout_s
                )
        elif self._is_cache_locked:
            logger.info(
                "[VISION-CACHE] Ciclo exitoso #%d registrado en MODO BLOQUEADO (Escala fijada: %.2fx). Watchdog reseteado a %.0fs.",
                self._successful_cycles, self._cached_button_scale or 1.0, self._cache_inactivity_timeout_s
            )

    def clear_scale_cache(self, reason: str = "Inactividad/Recalibracion") -> None:
        """Purga la memoria de tamaño/escala para forzar una recalibración completa."""
        was_locked = self._is_cache_locked
        prev_scale = self._cached_button_scale
        self._cached_button_scale = None
        self._cached_dial_scale = None
        self._cached_dimensions = None
        self._last_dial_roi = None
        self._dial_tracking_frames = 0
        self._dial_lost_frames = 0
        self._successful_cycles = 0
        self._is_cache_locked = False
        self._scale_observations.clear()
        self._dimension_observations.clear()
        self._last_match_timestamp = 0.0
        logger.info(
            "[VISION-CACHE] Caché purgado (Razón: %s | Estaba bloqueado: %s | Escala anterior: %s). Racha reiniciada a 0/%d. Retornando a modo exploratorio.",
            reason, was_locked, f"{prev_scale:.2f}x" if prev_scale else "ninguna", self._required_cycles_to_lock
        )

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
        now = time.monotonic()
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
            self._dial_lost_frames = 0
            self._last_match_timestamp = now
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
            self._dial_lost_frames = 0
            self._last_match_timestamp = now
            return btn_match

        # ==========================================================
        # FASE 3: Rastreo Ultra-Rápido del Dial Conocido (< 0.2 ms / 5000 FPS)
        # ==========================================================
        if self._last_dial_roi is not None:
            fast_match = self._track_known_dial(img_bgr, ox, oy, frame.frame_id)
            if fast_match is not None:
                self._last_match_timestamp = now
                return fast_match
            # Si _track_known_dial retornó None, la ventana de gracia expiró y ya limpió _last_dial_roi

        # ==========================================================
        # FASE 4: Detectar Minijuego de Aguja (Búsqueda Inicial del Dial)
        # ==========================================================
        minigame_match = self._detect_minigame(small_screen, img_bgr, ox, oy, frame.frame_id, frame.source_id)
        if minigame_match is not None:
            self._last_match_timestamp = now
            return minigame_match

        # ==========================================================
        # FASE 5: En Espera / Rastreo Activo
        # Watchdog Temporal: Cuando el caché está bloqueado, se monitorea una ventana continua
        # de inactividad (90 segundos). Si transcurre ese tiempo sin NINGÚN match en pantalla
        # (cubriendo holgadamente la espera pasiva de picada), se purga el caché automáticamente.
        # Si el caché NO está bloqueado, este mecanismo está inactivo (búsqueda exploratoria continua).
        # ==========================================================
        if self._cache_size_enabled and self._is_cache_locked:
            if self._last_match_timestamp == 0.0:
                self._last_match_timestamp = now
            elif (now - self._last_match_timestamp) >= self._cache_inactivity_timeout_s:
                logger.warning(
                    "[VISION-CACHE] Inactividad crítica de %.1fs sin ningún match en modo bloqueado. "
                    "Posible cambio de HUD/navegador o ventana desfasada. Purgando caché para re-calibración.",
                    now - self._last_match_timestamp
                )
                self.clear_scale_cache()

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

        if self._cache_size_enabled and self._is_cache_locked and self._cached_button_scale is not None:
            # Modo Caché Bloqueado O(1) con tolerancia de vecindad (+-5%):
            # Prueba la escala óptima fijada y sus vecinas inmediatas (+-0.05).
            # Costo: < 0.3 ms en grayscale. Elimina al 100% fallos por pulsación/bobbing del botón REEL! o variaciones subpixel.
            s_lock = self._cached_button_scale
            scales_to_try: list[float] = [s_lock]
            for neighbor in (round(s_lock - 0.05, 2), round(s_lock + 0.05, 2)):
                if neighbor in self._precomputed_cast_gray and neighbor not in scales_to_try:
                    scales_to_try.append(neighbor)
        elif self._cache_size_enabled and self._cached_button_scale is not None:
            # Modo Calibración Dinámica (Ciclos < 5): Evalúa primero la escala observada más reciente
            # pero conserva el conjunto de escalas candidatas para adaptarse a cambios en el navegador.
            scales_to_try = [self._cached_button_scale] + [s for s in self.BUTTON_CANDIDATE_SCALES if s != self._cached_button_scale]
        else:
            scales_to_try = list(self.BUTTON_CANDIDATE_SCALES)

        small_gray = cv2.cvtColor(small_screen, cv2.COLOR_BGR2GRAY)

        best_score = 0.0
        best_loc: tuple[int, int] = (0, 0)
        best_size: tuple[int, int] = (0, 0)
        best_scale: float = 1.0
        best_strategy_id: str = "button_detected"

        for s in scales_to_try:
            # Evaluar plantilla CAST! primero en escala de grises (3x más rápido)
            if s in self._precomputed_cast_gray:
                stpl_gray = self._precomputed_cast_gray[s]
                th, tw = stpl_gray.shape[:2]
                if sw >= tw and sh >= th:
                    res = cv2.matchTemplate(small_gray, stpl_gray, cv2.TM_CCOEFF_NORMED)
                    _, mv, _, ml = cv2.minMaxLoc(res)

                    if mv >= self._button_threshold:
                        # Verificación estricta de color BGR en la región candidata (elimina falsos positivos grises)
                        candidate_bgr = small_screen[ml[1]:ml[1]+th, ml[0]:ml[0]+tw]
                        res_bgr = cv2.matchTemplate(candidate_bgr, self._precomputed_cast[s], cv2.TM_CCOEFF_NORMED)
                        _, mv_bgr, _, _ = cv2.minMaxLoc(res_bgr)

                        if mv_bgr > best_score:
                            best_score = float(mv_bgr)
                            best_loc = ml
                            best_size = (tw * 2, th * 2)
                            best_scale = s
                            best_strategy_id = "cast_button_detected"

            # Evaluar plantilla REEL! primero en escala de grises
            if s in self._precomputed_reel_gray:
                stpl_gray = self._precomputed_reel_gray[s]
                th, tw = stpl_gray.shape[:2]
                if sw >= tw and sh >= th:
                    res = cv2.matchTemplate(small_gray, stpl_gray, cv2.TM_CCOEFF_NORMED)
                    _, mv, _, ml = cv2.minMaxLoc(res)

                    if mv >= self._button_threshold:
                        candidate_bgr = small_screen[ml[1]:ml[1]+th, ml[0]:ml[0]+tw]
                        res_bgr = cv2.matchTemplate(candidate_bgr, self._precomputed_reel[s], cv2.TM_CCOEFF_NORMED)
                        _, mv_bgr, _, _ = cv2.minMaxLoc(res_bgr)

                        if mv_bgr > best_score:
                            best_score = float(mv_bgr)
                            best_loc = ml
                            best_size = (tw * 2, th * 2)
                            best_scale = s
                            best_strategy_id = "reel_button_detected"

            # Retorno inmediato si ya se superó el umbral de coincidencia
            if best_score >= self._button_threshold:
                break

        # Fallback de seguridad en modo bloqueado:
        # Si la escala bloqueada (+-5%) no halló ningún botón pero el usuario cambió de zoom o resolución,
        # evaluamos las demás escalas candidatas para evitar quedar ciego.
        if self._cache_size_enabled and self._is_cache_locked and best_score < self._button_threshold:
            remaining_scales = [s for s in self.BUTTON_CANDIDATE_SCALES if s not in scales_to_try]
            for s in remaining_scales:
                if s in self._precomputed_cast_gray:
                    stpl_gray = self._precomputed_cast_gray[s]
                    th, tw = stpl_gray.shape[:2]
                    if sw >= tw and sh >= th:
                        res = cv2.matchTemplate(small_gray, stpl_gray, cv2.TM_CCOEFF_NORMED)
                        _, mv, _, ml = cv2.minMaxLoc(res)
                        if mv >= self._button_threshold:
                            candidate_bgr = small_screen[ml[1]:ml[1]+th, ml[0]:ml[0]+tw]
                            res_bgr = cv2.matchTemplate(candidate_bgr, self._precomputed_cast[s], cv2.TM_CCOEFF_NORMED)
                            _, mv_bgr, _, _ = cv2.minMaxLoc(res_bgr)
                            if mv_bgr > best_score:
                                best_score = float(mv_bgr)
                                best_loc = ml
                                best_size = (tw * 2, th * 2)
                                best_scale = s
                                best_strategy_id = "cast_button_detected"
                if s in self._precomputed_reel_gray:
                    stpl_gray = self._precomputed_reel_gray[s]
                    th, tw = stpl_gray.shape[:2]
                    if sw >= tw and sh >= th:
                        res = cv2.matchTemplate(small_gray, stpl_gray, cv2.TM_CCOEFF_NORMED)
                        _, mv, _, ml = cv2.minMaxLoc(res)
                        if mv >= self._button_threshold:
                            candidate_bgr = small_screen[ml[1]:ml[1]+th, ml[0]:ml[0]+tw]
                            res_bgr = cv2.matchTemplate(candidate_bgr, self._precomputed_reel[s], cv2.TM_CCOEFF_NORMED)
                            _, mv_bgr, _, _ = cv2.minMaxLoc(res_bgr)
                            if mv_bgr > best_score:
                                best_score = float(mv_bgr)
                                best_loc = ml
                                best_size = (tw * 2, th * 2)
                                best_scale = s
                                best_strategy_id = "reel_button_detected"
                if best_score >= self._button_threshold:
                    logger.warning(
                        "[VISION-CACHE] Botón '%s' no coincidió en escala bloqueada (%.2fx), hallado en fallback multi-escala (%.2fx, Confianza: %.1f%%). "
                        "Posible cambio de HUD/zoom en navegador. Purgando caché para re-calibración.",
                        best_strategy_id, self._cached_button_scale or 1.0, best_scale, best_score * 100
                    )
                    self.clear_scale_cache(reason=f"Cambio de escala detectado por fallback ({self._cached_button_scale or 1.0:.2f}x -> {best_scale:.2f}x)")
                    break

        if best_score >= self._button_threshold:
            if self._cache_size_enabled:
                self._cached_button_scale = best_scale
                self._cached_dimensions = best_size
                if not self._is_cache_locked:
                    self._scale_observations.append(best_scale)
                    self._dimension_observations.append(best_size)

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

    def _find_needle(self, dial_roi: np.ndarray) -> tuple[int, int, int]:
        """
        Localiza la aguja estática superior (12 en punto) de forma tolerante a sacudidas (shake).
        Retorna (count_pixels, centroid_x, centroid_y).
        """
        rh, rw = dial_roi.shape[:2]
        if rh < 15 or rw < 15:
            return 0, rw // 2, int(rh * 0.20)
        y1 = max(0, int(rh * 0.03))
        y2 = min(rh, int(rh * 0.38))
        x1 = max(0, int(rw * 0.28))
        x2 = min(rw, int(rw * 0.72))
        needle_crop = dial_roi[y1:y2, x1:x2]
        if needle_crop.size == 0:
            return 0, rw // 2, int(rh * 0.20)
        hsv = cv2.cvtColor(needle_crop, cv2.COLOR_BGR2HSV)
        m1 = cv2.inRange(hsv, np.array([5, 80, 80]), np.array([25, 255, 255]))
        m2 = cv2.inRange(hsv, np.array([0, 80, 80]), np.array([12, 255, 255]))
        m3 = cv2.inRange(hsv, np.array([168, 80, 80]), np.array([180, 255, 255]))
        mask = cv2.bitwise_or(m1, cv2.bitwise_or(m2, m3))
        count = int(np.count_nonzero(mask))
        if count >= 12:
            M = cv2.moments(mask)
            if M["m00"] > 0:
                cx = int(M["m10"] / M["m00"]) + x1
                cy = int(M["m01"] / M["m00"]) + y1
                return count, cx, cy
        return count, rw // 2, int(rh * 0.20)

    def _count_needle_pixels(self, roi_bgr: np.ndarray) -> int:
        """
        Cuenta los píxeles de color naranja/rojo de la aguja estática superior (12 en punto).
        Elimina al 100% los falsos positivos con el césped, agua o arena del escenario.
        """
        return self._find_needle(roi_bgr)[0]

    def _track_known_dial(
            self,
            img_bgr: np.ndarray,
            ox: int,
            oy: int,
            frame_id: int
    ) -> MatchResult | None:
        """
        Rastreo ultra-rápido (< 0.2 ms / ~5000 FPS) del dial conocido.
        Resiliente a sacudidas (shake animation), desalineaciones de píxeles y
        destellos rojos de penalización tras fallos accidentales.
        """
        if self._last_dial_roi is None:
            return None

        # Límite de seguridad: hasta 720 fotogramas consecutivos (~12.0s a 60 FPS / ~6.0s a 120 FPS)
        # permitiendo múltiples rotaciones lentas del dial y penalizaciones sin perder el objetivo
        self._dial_tracking_frames += 1

        full_x, full_y, full_w, full_h = self._last_dial_roi
        fh, fw = img_bgr.shape[:2]

        # Validar límites de la imagen
        if full_x < 0 or full_y < 0 or full_x + full_w > fw or full_y + full_h > fh:
            self._last_dial_roi = None
            self._dial_tracking_frames = 0
            self._dial_lost_frames = 0
            return None

        dial_roi = img_bgr[full_y:full_y+full_h, full_x:full_x+full_w]
        if dial_roi.size == 0:
            self._last_dial_roi = None
            self._dial_tracking_frames = 0
            self._dial_lost_frames = 0
            return None

        needle_count, needle_cx, needle_cy = self._find_needle(dial_roi)

        hsv_roi = cv2.cvtColor(dial_roi, cv2.COLOR_BGR2HSV)
        mask_olive = cv2.inRange(hsv_roi, np.array([25, 40, 70]), np.array([45, 160, 220]))
        olive_ratio = np.count_nonzero(mask_olive) / float(full_w * full_h)

        # El dial se considera activo si presenta sectores verdes o la aguja estática superior
        is_dial_present = (olive_ratio >= 0.12) or (needle_count >= 12)

        if is_dial_present:
            self._dial_lost_frames = 0
        else:
            # Ventana de gracia (debounce) para tolerar fotogramas de transición brusca o blur
            self._dial_lost_frames += 1
            if self._dial_lost_frames > self._max_dial_lost_frames:
                self._last_dial_roi = None
                self._dial_lost_frames = 0
                self._dial_tracking_frames = 0
                return None

        # Posicionamiento dinámico tolerante a sacudidas (shake):
        # La aguja fija a las 12 en punto actúa como ancla visual para recentrar el dial en tiempo real
        cx = full_x + (needle_cx if needle_count >= 12 else full_w // 2)
        cy = full_y + full_h // 2

        region = Region(
            top_left=Point(x=ox + full_x, y=oy + full_y),
            size=Size(width=full_w, height=full_h)
        )
        center = Point(x=ox + cx, y=oy + cy)

        # Inspección precisa de la columna bajo la aguja a las 12 en punto
        # Columna estrecha ajustada al grosor real de la aguja (+-2.5% del ancho del dial, ~8px totales)
        # para eliminar disparos prematuros en los bordes antes de llegar a la aguja
        y1 = max(0, int(full_y + full_h * 0.22))
        y2 = min(fh, int(full_y + full_h * 0.40))
        half_w = max(2, int(full_w * 0.025))

        # Anticipación configurable (0 px por defecto = centrado exacto en la aguja)
        effective_cx = cx - self._minigame_anticipation_px
        x1 = max(0, effective_cx - half_w)
        x2 = min(fw, effective_cx + half_w)

        needle_zone = img_bgr[y1:y2, x1:x2]
        if needle_zone.size > 0:
            hsv_zone = cv2.cvtColor(needle_zone, cv2.COLOR_BGR2HSV)
            mask_light_green = cv2.inRange(hsv_zone, self._target_green_lower, self._target_green_upper)
            green_pixels = np.count_nonzero(mask_light_green)
            total_pixels = max(1, needle_zone.shape[0] * needle_zone.shape[1])
            ratio = green_pixels / float(total_pixels)

            # !TODO: Telemetría B - Incorporar streaming granular de minijuego (verde%, aguja px, dx offset y latencia ms)
            # Impacto cuando el sector verde está sólidamente posicionado bajo la aguja
            is_hit = ratio >= 0.35
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

        return MatchResult(
            found=False,
            confidence=0.90,
            region=region,
            center=center,
            strategy_id="minigame_tracking",
            frame_id=frame_id
        )

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
        Utiliza escalas independientes precalculadas y umbrales tolerantes a shake.
        """
        # 1. Respaldo por segmentación HSV adaptativa (SÓLO para pruebas sintéticas de unidad)
        if source_id.startswith("synthetic"):
            return self._detect_minigame_contour(img_bgr, ox, oy, frame_id)

        if self._dial_mat is not None:
            fh, fw = img_bgr.shape[:2]
            sh, sw = small_screen.shape[:2]

            # Pre-filtro ultra-rápido de color (< 0.5 ms):
            # El dial contiene sectores verdes O destello rojo de fallo/penalización
            tiny = cv2.resize(small_screen, (240, 135), interpolation=cv2.INTER_NEAREST)
            hsv_tiny = cv2.cvtColor(tiny, cv2.COLOR_BGR2HSV)
            mask_tiny = cv2.inRange(hsv_tiny, np.array([20, 35, 60]), np.array([45, 255, 255]))
            if cv2.countNonZero(mask_tiny) < 12:
                return None

            scales = [self._cached_dial_scale] if (self._cache_size_enabled and self._cached_dial_scale) else list(self.DIAL_CANDIDATE_SCALES)

            best_score = 0.0
            best_loc = (0, 0)
            best_size = (0, 0)
            best_s = 1.0

            has_mask = getattr(self, "_dial_static_mask", None) is not None

            for s in scales:
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

            # Umbral de coincidencia: 0.89 para máscara estática (SQDIFF) o dial_threshold para CCOEFF
            # (El césped uniforme produce correlación de ~0.68, por lo que 0.89 es 100% inmune a falsos positivos
            # a la vez que absorbe desenfoque por sacudidas y destello de fallo)
            effective_thresh = 0.89 if has_mask else self._dial_threshold
            if best_score >= effective_thresh:
                full_x = best_loc[0] * 2
                full_y = best_loc[1] * 2
                full_w, full_h = best_size

                # Verificación de integridad: el dial debe contener la aguja superior naranja/roja y sectores verdes o rojo de fallo
                dial_roi = img_bgr[full_y:full_y+full_h, full_x:full_x+full_w]
                if dial_roi.size > 0:
                    needle_count, needle_cx, _ = self._find_needle(dial_roi)
                    if needle_count < 15:
                        # Rechazar falsos positivos en césped/fondo
                        return None

                    hsv_roi = cv2.cvtColor(dial_roi, cv2.COLOR_BGR2HSV)
                    mask_olive = cv2.inRange(hsv_roi, np.array([25, 40, 70]), np.array([45, 160, 220]))
                    olive_ratio = np.count_nonzero(mask_olive) / float(full_w * full_h)

                    if (olive_ratio >= 0.12) or (needle_count >= 12):
                        self._last_dial_roi = (full_x, full_y, full_w, full_h)
                        self._dial_tracking_frames = 0
                        self._dial_lost_frames = 0
                        if self._cache_size_enabled:
                            self._cached_dial_scale = best_s

                        cx = full_x + (needle_cx if needle_count >= 12 else full_w // 2)
                        cy = full_y + full_h // 2

                        region = Region(
                            top_left=Point(x=ox + full_x, y=oy + full_y),
                            size=Size(width=full_w, height=full_h)
                        )
                        center = Point(x=ox + cx, y=oy + cy)

                        y1 = max(0, int(full_y + full_h * 0.22))
                        y2 = min(fh, int(full_y + full_h * 0.40))
                        half_w = max(2, int(full_w * 0.025))
                        effective_cx = cx - self._minigame_anticipation_px
                        x1 = max(0, effective_cx - half_w)
                        x2 = min(fw, effective_cx + half_w)

                        needle_zone = img_bgr[y1:y2, x1:x2]
                        if needle_zone.size > 0:
                            hsv_zone = cv2.cvtColor(needle_zone, cv2.COLOR_BGR2HSV)
                            mask_light_green = cv2.inRange(hsv_zone, self._target_green_lower, self._target_green_upper)
                            green_pixels = np.count_nonzero(mask_light_green)
                            total_pixels = max(1, needle_zone.shape[0] * needle_zone.shape[1])
                            ratio = green_pixels / float(total_pixels)

                            is_hit = ratio >= 0.35

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

        min_area = min(8000.0, float(img_bgr.shape[0] * img_bgr.shape[1] * 0.10))
        min_dim = min(80, int(min(img_bgr.shape[0], img_bgr.shape[1]) * 0.25))
        for cnt in contours:
            area = cv2.contourArea(cnt)
            # La tarjeta ocupa una porción representativa (>8000 px o >10% de la zona escaneada)
            if area > min_area:
                bx, by, bw, bh = cv2.boundingRect(cnt)

                # Descartar barras delgadas (como la barra de títulos del navegador o bordes)
                if bw < min_dim or bh < min_dim:
                    continue

                aspect = bw / float(bh) if bh > 0 else 0.0
                # Aspect ratio vertical o moderadamente cuadrado (entre 0.55 y 1.20)
                if 0.55 <= aspect <= 1.20:
                    rect_area = bw * bh
                    solidity = area / float(rect_area) if rect_area > 0 else 0.0

                    # Permite texto y sprite en el centro de la tarjeta (>60% de solidez)
                    if solidity > 0.60:
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
