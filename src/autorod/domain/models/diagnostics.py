from collections.abc import Sequence
from dataclasses import dataclass, field
from autorod.domain.models.image_payload import ImagePayload
from autorod.domain.models.geometry import Region


@dataclass(frozen=True, slots=True, kw_only=True)
class DiagnosticFrame:
    """
    Fotograma procesado, enriquecido con metadatos para renderizado.
    Separado de la matriz subyacente para no depender de dependencias gráficas.
    Garantiza inmutabilidad profunda de colecciones internas.
    """
    payload: ImagePayload
    layer_name: str
    bounding_boxes: Sequence[Region] = field(default_factory=tuple)
    labels: Sequence[str] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not isinstance(self.bounding_boxes, tuple):
            object.__setattr__(self, "bounding_boxes", tuple(self.bounding_boxes))
        if not isinstance(self.labels, tuple):
            object.__setattr__(self, "labels", tuple(self.labels))
