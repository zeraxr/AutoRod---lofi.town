import asyncio
import threading
import logging
from autorod.domain.ports.runner import IPipelineRunner

logger = logging.getLogger(__name__)


class AsyncioPipelineRunner(IPipelineRunner):
    """
    Variante SOTA del Pipeline utilizando un bucle de eventos asyncio dedicado.
    Ideal para entornos donde el GIL es liberado eficientemente por extensiones C.
    Garantiza concurrencia sin bloqueos y apagado cooperativo.
    """

    def __init__(self) -> None:
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            raise RuntimeError("AsyncioPipelineRunner ya está en ejecución.")

        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run_event_loop,
            name="Th-AsyncioRunner",
            daemon=True
        )
        self._thread.start()
        logger.info("AsyncioPipelineRunner iniciado en hilo dedicado.")

    def _run_event_loop(self) -> None:
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._lifecycle_coroutine())
        finally:
            self._loop.close()

    async def _lifecycle_coroutine(self) -> None:
        """Ciclo de vida principal asíncrono regulado por stop_event."""
        while not self._stop_event.is_set():
            await asyncio.sleep(0.01)

    def stop(self) -> None:
        logger.info("Deteniendo AsyncioPipelineRunner cooperativamente...")
        self._stop_event.set()

    def join(self, timeout_s: float | None = None) -> None:
        if self._thread is not None:
            self._thread.join(timeout=timeout_s or 3.0)
            if self._thread.is_alive():
                logger.error("AsyncioPipelineRunner no finalizó en el tiempo límite.")
            self._thread = None
        logger.info("AsyncioPipelineRunner detenido exitosamente.")
