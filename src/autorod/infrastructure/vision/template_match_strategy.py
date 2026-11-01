import cv2
from autorod.domain.ports.vision import IVisionStrategy
from autorod.domain.models.image_payload import ImagePayload
from autorod.domain.models.match_result import MatchResult
from autorod.domain.models.geometry import Point, Size, Region
from autorod.infrastructure.imaging.numpy_bridge import payload_to_ndarray


class TemplateMatchStrategy(IVisionStrategy):
    """
    Estrategia de visión basada en cv2.matchTemplate (correlación cruzada normalizada).
    Orquesta la deducción matemática manteniendo la inmutabilidad del dominio.
    """

    def __init__(
            self,
            template: ImagePayload | None = None,
            threshold: float = 0.8,
            strategy_id: str = "sota_template_match"
    ) -> None:
        self._strategy_id = strategy_id
        self._threshold = threshold
        self._template_payload = template
        self._cached_template_mat = payload_to_ndarray(template) if template else None

    @property
    def strategy_id(self) -> str:
        return self._strategy_id

    def set_template(self, template: ImagePayload) -> None:
        """Actualiza la plantilla de búsqueda."""
        self._template_payload = template
        self._cached_template_mat = payload_to_ndarray(template)

    def analyze(self, frame: ImagePayload, template_ref: str | None = None) -> MatchResult:
        """
        Ejecuta coincidencia de plantilla entre el fotograma y la imagen de referencia.
        """
        if self._cached_template_mat is None:
            return MatchResult(
                found=False,
                confidence=0.0,
                region=None,
                center=None,
                strategy_id=self.strategy_id,
                frame_id=frame.frame_id
            )

        frame_mat = payload_to_ndarray(frame)
        tpl_mat = self._cached_template_mat

        # Si el fotograma es menor que la plantilla, no es posible el match
        if frame_mat.shape[0] < tpl_mat.shape[0] or frame_mat.shape[1] < tpl_mat.shape[1]:
            return MatchResult(
                found=False,
                confidence=0.0,
                region=None,
                center=None,
                strategy_id=self.strategy_id,
                frame_id=frame.frame_id
            )

        res = cv2.matchTemplate(frame_mat, tpl_mat, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(res)

        confidence = max(0.0, min(1.0, float(max_val)))
        found = confidence >= self._threshold

        tpl_h, tpl_w = tpl_mat.shape[:2]
        ox = frame.offset_x
        oy = frame.offset_y
        if found:
            region = Region(
                top_left=Point(x=int(ox + max_loc[0]), y=int(oy + max_loc[1])),
                size=Size(width=int(tpl_w), height=int(tpl_h))
            )
            center = Point(
                x=int(ox + max_loc[0] + tpl_w // 2),
                y=int(oy + max_loc[1] + tpl_h // 2)
            )
        else:
            region = None
            center = None

        return MatchResult(
            found=found,
            confidence=confidence,
            region=region,
            center=center,
            strategy_id=self.strategy_id,
            frame_id=frame.frame_id
        )
