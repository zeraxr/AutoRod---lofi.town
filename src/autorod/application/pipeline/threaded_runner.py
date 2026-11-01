from autorod.domain.ports.runner import IPipelineRunner
from autorod.application.pipeline.supervisor import PipelineSupervisor


class ThreadedPipelineRunner(IPipelineRunner):
    """Adaptador que cumple el contrato Runner envolviendo al Supervisor."""

    def __init__(self, supervisor: PipelineSupervisor) -> None:
        self._supervisor = supervisor

    @property
    def supervisor(self) -> PipelineSupervisor:
        return self._supervisor

    def start(self) -> None:
        self._supervisor.start()

    def stop(self) -> None:
        self._supervisor.stop()

    def join(self, timeout_s: float | None = None) -> None:
        self._supervisor.join(timeout_s or 3.0)
