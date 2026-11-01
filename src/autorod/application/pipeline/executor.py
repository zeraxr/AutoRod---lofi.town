import queue
import logging
from typing import Any
from autorod.domain.ports.input_simulator import IInputSimulator
from autorod.domain.ports.actions import IBotTask
from autorod.application.pipeline.queues import _STOP

logger = logging.getLogger(__name__)


class ActionExecutor:
    """
    Consume MatchResults, evalúa la tarea y dispara I/O de hardware.
    Permite activar/pausar la emisión física de acciones sin detener el flujo visual.
    """

    def __init__(
            self,
            action_queue: queue.Queue[Any],
            task: IBotTask,
            simulator: IInputSimulator,
            enabled: bool = True
    ) -> None:
        self._queue = action_queue
        self._task = task
        self._simulator = simulator
        self._enabled = enabled

    @property
    def is_enabled(self) -> bool:
        return self._enabled

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, val: bool) -> None:
        self._enabled = bool(val)
        if hasattr(self._task, "enabled"):
            self._task.enabled = self._enabled

    def set_enabled(self, enabled: bool) -> None:
        """Activa o desactiva la inyección física de clics/movimientos."""
        self.enabled = enabled

    @property
    def simulator(self) -> IInputSimulator:
        return self._simulator

    @simulator.setter
    def simulator(self, sim: IInputSimulator) -> None:
        self._simulator = sim

    def run(self) -> None:
        try:
            while True:
                item = self._queue.get()
                if item is _STOP:
                    self._queue.task_done()
                    break

                if self._enabled:
                    commands = self._task.evaluate(item)
                    if commands:
                        logger.info("[ACCION] Inyectando %d comandos de hardware en pantalla...", len(commands))
                        self._simulator.execute_batch(commands)

                self._queue.task_done()
        finally:
            self._simulator.close()
