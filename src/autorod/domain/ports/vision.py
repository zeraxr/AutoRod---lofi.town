from typing import Protocol
from autorod.domain.models.image_payload import ImagePayload
from autorod.domain.models.match_result import MatchResult


class IVisionStrategy(Protocol):
    """
    Contrato matemático puro para orquestadores visuales.
    Debe ser hilo-seguro y carecer de estado mutable o E/S.
    """

    @property
    def strategy_id(self) -> str:
        """Identificador de la heurística implementada."""
        ...

    def analyze(
            self, frame: ImagePayload, template_ref: str | None = None
    ) -> MatchResult:
        """
        Evalúa un fotograma para dictaminar colisión de entidades.

        Args:
            frame: Objeto de transferencia binario y agnóstico.
            template_ref: Clave identificadora opcional del recurso ideal.

        Returns:
            MatchResult: Dictamen matemático de convergencia visual.
        """
        ...