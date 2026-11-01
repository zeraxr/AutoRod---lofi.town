from typing import Protocol
from collections.abc import Sequence
from autorod.domain.models.input_commands import InputCommand


class IInputSimulator(Protocol):
    """
    Contrato abstracto para inyectores Ring 0 y/o Userland.
    Garantiza atomicidad y retención del orden de ejecución.
    """

    def execute(self, command: InputCommand) -> None:
        """
        Inyecta un único evento al sistema operativo.
        """
        ...

    def execute_batch(self, commands: Sequence[InputCommand]) -> None:
        """
        Inyecta una serie de comandos garantizando un buffer sin interrupciones OS.
        """
        ...

    def close(self) -> None:
        """Libera el contexto del driver (esencial para Interception)."""
        ...