from typing import Protocol
from collections.abc import Sequence
from autorod.domain.models.match_result import MatchResult
from autorod.domain.models.input_commands import InputCommand


class IBotTask(Protocol):
    """
    Unidad de negocio SOTA. Transforma deducciones en acciones.
    """

    def evaluate(self, result: MatchResult) -> Sequence[InputCommand]:
        """
        Genera rutinas (ej: spam_click) basándose en la exactitud y posición del match.
        """
        ...