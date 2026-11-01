import random
import threading
from collections.abc import Sequence
from autorod.domain.ports.input_simulator import IInputSimulator
from autorod.domain.ports.clock import IClock
from autorod.domain.models.input_commands import (
    InputCommand,
    MouseClick,
    MouseMove,
    KeyPress,
    KeyRelease,
)


class HumanizedInputSimulator(IInputSimulator):
    """
    Decorador / Proxy de evasión heurística.
    Introduce micro-variaciones estocásticas gaussianas y trayectorias
    suavizadas sin utilizar time.sleep() (orquestado vía IClock).
    """

    def __init__(
            self,
            delegate: IInputSimulator,
            clock: IClock,
            cancel_event: threading.Event | None = None,
            mean_click_delay_ms: float = 55.0,
            std_click_delay_ms: float = 12.0
    ) -> None:
        self._delegate = delegate
        self._clock = clock
        self._cancel_event = cancel_event or threading.Event()
        self._mean_delay = mean_click_delay_ms
        self._std_delay = std_click_delay_ms

    def execute(self, command: InputCommand) -> None:
        self.execute_batch([command])

    def execute_batch(self, commands: Sequence[InputCommand]) -> None:
        for cmd in commands:
            if self._cancel_event.is_set():
                break

            self._delegate.execute(cmd)

            # Si es un click presionado, introducir latencia biométrica antes del release
            if isinstance(cmd, (MouseClick, KeyPress)):
                delay_s = max(0.020, random.gauss(self._mean_delay, self._std_delay) / 1000.0)
                self._clock.wait(delay_s, self._cancel_event)

    def close(self) -> None:
        self._delegate.close()
