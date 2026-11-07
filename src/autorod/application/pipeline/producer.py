import logging
import threading
from typing import Any
from autorod.domain.ports.capture import ICaptureSource
from autorod.domain.ports.clock import IClock
from autorod.application.pipeline.queues import LatestFrameQueue, _STOP


logger = logging.getLogger(__name__)


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

    @property
    def target_fps(self) -> int:
        if self._interval_s <= 0:
            return 60
        return int(round(1.0 / self._interval_s))

    @target_fps.setter
    def target_fps(self, fps: int) -> None:
        if fps > 0:
            self._interval_s = 1.0 / fps

    def stop(self) -> None:
        self._stop_event.set()

    def run(self) -> None:
        """Bucle infinito de ingesta, regulado cooperativamente con tolerancia a fallos transitorios."""
        consecutive_errors = 0
        try:
            self._source.start()
            while not self._stop_event.is_set():
                start_time = self._clock.monotonic_ns()

                try:
                    # grab() retorna ImagePayload (memoria inmutable ya copiada)
                    payload = self._source.grab()
                    self._queue.put_latest(payload)
                    consecutive_errors = 0
                except Exception as exc:
                    consecutive_errors += 1
                    if consecutive_errors == 1 or consecutive_errors % 60 == 0:
                        logger.warning(
                            "Fallo transitorio en captura de pantalla (%d consecutivos): %s",
                            consecutive_errors,
                            exc
                        )
                    # Si falla reiteradamente (ej. cambio de monitor o bloqueo DWM),
                    # reiniciar el contexto del adaptador de captura para recuperar el handle Win32.
                    if consecutive_errors >= 5:
                        try:
                            self._source.stop()
                            self._clock.wait(0.1, self._stop_event)
                            self._source.start()
                        except Exception:
                            pass
                    self._clock.wait(0.05, self._stop_event)
                    continue

                elapsed_s = (self._clock.monotonic_ns() - start_time) / 1e9
                sleep_time = self._interval_s - elapsed_s
                if sleep_time > 0:
                    self._clock.wait(sleep_time, self._stop_event)

        except Exception as exc:
            logger.error("Error imprevisto fatal en bucle de captura del productor: %s", exc, exc_info=True)
        finally:
            self._source.stop()
            self._queue.put_latest(_STOP)
