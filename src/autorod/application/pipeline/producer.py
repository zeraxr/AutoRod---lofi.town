import threading
from typing import Any
from autorod.domain.ports.capture import ICaptureSource
from autorod.domain.ports.clock import IClock
from autorod.application.pipeline.queues import LatestFrameQueue, _STOP


class CaptureProducer:
    """Extrae fotogramas del adaptador Ring 3 y los encola copiándolos."""

    def __init__(
            self,
            source: ICaptureSource,
            frame_queue: LatestFrameQueue[Any],
            clock: IClock,
            target_fps: int = 60
    ) -> None:
        self._source = source
        self._queue = frame_queue
        self._clock = clock
        self._interval_s = 1.0 / target_fps
        self._stop_event = threading.Event()

    def stop(self) -> None:
        self._stop_event.set()

    def run(self) -> None:
        """Bucle infinito de ingesta, regulado cooperativamente."""
        try:
            self._source.start()
            while not self._stop_event.is_set():
                start_time = self._clock.monotonic_ns()

                # grab() retorna ImagePayload (memoria inmutable ya copiada)
                payload = self._source.grab()
                self._queue.put_latest(payload)

                elapsed_s = (self._clock.monotonic_ns() - start_time) / 1e9
                sleep_time = self._interval_s - elapsed_s
                if sleep_time > 0:
                    self._clock.wait(sleep_time, self._stop_event)

        finally:
            self._source.stop()
            self._queue.put_latest(_STOP)