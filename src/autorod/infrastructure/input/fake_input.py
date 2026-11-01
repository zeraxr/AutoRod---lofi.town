from collections.abc import Sequence
from autorod.domain.ports.input_simulator import IInputSimulator
from autorod.domain.models.input_commands import InputCommand


class FakeInputSimulator(IInputSimulator):
    """Adaptador que almacena comandos en memoria para aserciones de testing."""
    def __init__(self) -> None:
        self.history: list[InputCommand] = []

    def execute(self, command: InputCommand) -> None:
        self.history.append(command)

    def execute_batch(self, commands: Sequence[InputCommand]) -> None:
        self.history.extend(commands)

    def close(self) -> None:
        pass