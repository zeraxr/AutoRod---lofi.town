import queue
from autorod.infrastructure.ui.tk.diagnostics_view import DiagnosticsCanvasView
from autorod.infrastructure.diagnostics.queue_sink import QueueDiagnosticsSink
from autorod.domain.ports.diagnostics import IDiagnosticsRenderer


class DiagnosticsPresenter:
    """MVP: Extrae del Queue de dominio, renderiza vía adaptador y actualiza la Vista Tkinter."""

    def __init__(
            self,
            view: DiagnosticsCanvasView,
            sink: QueueDiagnosticsSink,
            renderer: IDiagnosticsRenderer
    ) -> None:
        self.view = view
        self.sink = sink
        self.renderer = renderer

    def start_polling(self, interval_ms: int = 33) -> None:
        """Bucle basado en after() para nunca bloquear Tkinter."""
        self._tick(interval_ms)

    def _tick(self, interval_ms: int) -> None:
        latest = None
        # Drenar cola conservando solo el más nuevo (sin bloquear)
        while True:
            try:
                latest = self.sink.q.get_nowait()
            except queue.Empty:
                break

        if latest:
            # Operación intensiva pero aislada en backend C (cv2)
            img_bytes = self.renderer.render(latest)
            self.view.update_image(img_bytes)

        self.view.after(interval_ms, lambda: self._tick(interval_ms))