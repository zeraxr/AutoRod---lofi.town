from dataclasses import dataclass
from autorod.domain.models.geometry import Point, Region


@dataclass(frozen=True, slots=True, kw_only=True)
class MatchResult:
    """
    Dictamen matemático puro de una estrategia de visión.

    Attributes:
        found: Indica si se superó el umbral de coincidencia.
        confidence: Nivel de confianza entre 0.0 y 1.0.
        strategy_id: Identificador de la heurística que resolvió el match.
        region: Bounding box de la detección, si aplica.
        center: Centro de masa absoluto de la coincidencia.
        frame_id: Referencia al fotograma analizado.
    """
    found: bool
    confidence: float
    strategy_id: str
    region: Region | None = None
    center: Point | None = None
    frame_id: int = 0

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("La confianza debe estar entre 0.0 y 1.0")
