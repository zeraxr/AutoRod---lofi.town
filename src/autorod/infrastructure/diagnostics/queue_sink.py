import queue
from autorod.domain.ports.diagnostics import IDiagnosticsSink
from autorod.domain.models.diagnostics import DiagnosticFrame


class QueueDiagnosticsSink(IDiagnosticsSink):
    """Sumidero seguro entre hilos con política de descarte para UI."""

    def __init__(self, maxsize: int = 2) -> None:
        self.q: queue.Queue[DiagnosticFrame] = queue.Queue(maxsize=maxsize)

    def publish(self, frame: DiagnosticFrame) -> None:
        try:
            self.q.put_nowait(frame)
        except queue.Full:
            try:
                self.q.get_nowait()
                self.q.put_nowait(frame)
            except (queue.Empty, queue.Full):
                pass