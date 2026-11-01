import cv2
import numpy as np
from autorod.domain.ports.vision import IVisionStrategy
from autorod.domain.models.image_payload import ImagePayload
from autorod.domain.models.match_result import MatchResult
from autorod.domain.models.geometry import Point, Size, Region
from autorod.infrastructure.imaging.numpy_bridge import payload_to_ndarray


class HsvContourStrategy(IVisionStrategy):
    """
    Motor de visión invariante a escala basado en filtrado HSV y análisis geométrico.
    Resuelve 'La Paradoja del Zoom' sin dependencias pesadas de ML (YOLO).
    """

    def __init__(
            self,
            lower_hsv: tuple[int, int, int] = (35, 100, 100),   # Verde / Target por defecto
            upper_hsv: tuple[int, int, int] = (85, 255, 255),
            min_area: float = 100.0,
            max_area: float = 500000.0,
            min_circularity: float = 0.0,
            strategy_id: str = "hsv_geometric_contour"
    ) -> None:
        self._strategy_id = strategy_id
        self._lower_hsv = np.array(lower_hsv, dtype=np.uint8)
        self._upper_hsv = np.array(upper_hsv, dtype=np.uint8)
        self._min_area = min_area
        self._max_area = max_area
        self._min_circularity = min_circularity

    @property
    def strategy_id(self) -> str:
        return self._strategy_id

    def set_hsv_range(
            self,
            lower: tuple[int, int, int],
            upper: tuple[int, int, int]
    ) -> None:
        """Permite calibración dinámica de colores."""
        self._lower_hsv = np.array(lower, dtype=np.uint8)
        self._upper_hsv = np.array(upper, dtype=np.uint8)

    def analyze(self, frame: ImagePayload, template_ref: str | None = None) -> MatchResult:
        """
        Segmenta el espacio de color HSV, aísla contornos y dictamina
        coincidencia geométrica independiente de la escala de zoom.
        """
        img_bgr = payload_to_ndarray(frame)
        hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)

        # 1. Máscara de color
        mask = cv2.inRange(hsv, self._lower_hsv, self._upper_hsv)

        # 2. Operaciones morfológicas para eliminar ruido
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
        mask = cv2.morphologyEx(mask, cv2.MORPH_DILATE, kernel, iterations=1)

        # 3. Detección de contornos geométricos
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        best_contour = None
        best_area = 0.0

        for c in contours:
            area = cv2.contourArea(c)
            if area < self._min_area or area > self._max_area:
                continue

            if self._min_circularity > 0.0:
                perimeter = cv2.arcLength(c, True)
                if perimeter > 0:
                    circularity = 4 * np.pi * (area / (perimeter * perimeter))
                    if circularity < self._min_circularity:
                        continue

            if area > best_area:
                best_area = area
                best_contour = c

        if best_contour is not None and best_area > 0:
            x, y, w, h = cv2.boundingRect(best_contour)
            m = cv2.moments(best_contour)
            if m["m00"] != 0:
                cx = int(m["m10"] / m["m00"])
                cy = int(m["m01"] / m["m00"])
            else:
                cx = x + w // 2
                cy = y + h // 2

            region = Region(
                top_left=Point(x=x, y=y),
                size=Size(width=w, height=h)
            )
            center = Point(x=cx, y=cy)
            confidence = min(1.0, float(best_area / (w * h if w * h > 0 else 1.0)))

            return MatchResult(
                found=True,
                confidence=confidence,
                region=region,
                center=center,
                strategy_id=self.strategy_id,
                frame_id=frame.frame_id
            )

        return MatchResult(
            found=False,
            confidence=0.0,
            region=None,
            center=None,
            strategy_id=self.strategy_id,
            frame_id=frame.frame_id
        )
