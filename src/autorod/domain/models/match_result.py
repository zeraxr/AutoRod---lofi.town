from dataclasses import dataclass
from autorod.domain.models.geometry import Point, Region


@dataclass(frozen=True, slots=True, kw_only=True)
class MatchResult:
    """
    Dictamen matemático puro de una estrategia de visión.

    Attributes:
        found: Indica si se superó el umbral de coincidencia.
        confidence: Nivel de confianza entre 0.0 y 1.0.
        region: Bounding box de la detección, si aplica.
        center: Centro de masa absoluto de la coincidencia.
        strategy_id: Identificador de la heurística que resolvió el match.
        frame_id: Referencia al fotograma analizado.
    """
    found: bool
    confidence: float
    region: Region | None
    center: Point | None
    strategy_id: str
    frame_id: int

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("La confianza debe estar entre 0.0 y 1.0")