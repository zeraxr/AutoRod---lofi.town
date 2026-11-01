import queue
import threading
from typing import TypeVar, Generic

T = TypeVar('T')
# Centinela para apagado cooperativo. Ningún consumidor debe procesarlo.
_STOP = object()


class LatestFrameQueue(Generic[T]):
    """
    Cola acotada con política "Latest-Frame-Wins" (LIFO con descarte).
    Si la cola está llena, descarta silenciosamente el elemento más antiguo.
    Hilos-segura con conteo atómico de descartes.
    """
    def __init__(self, maxsize: int = 1) -> None:
        self._q: queue.Queue[T] = queue.Queue(maxsize=maxsize)
        self._lock = threading.Lock()
        self._dropped_count = 0

    @property
    def dropped_count(self) -> int:
        """Retorna el total de fotogramas descartados de forma hilo-segura."""
        with self._lock:
            return self._dropped_count

    def put_latest(self, item: T) -> None:
        """
        Inserta el elemento. Si la cola está llena, hace un get no bloqueante
        (descartando el anterior) y vuelve a intentar.
        """
        while True:
            try:
                self._q.put_nowait(item)
                break
            except queue.Full:
                try:
                    self._q.get_nowait()
                    with self._lock:
                        self._dropped_count += 1
                except queue.Empty:
                    pass

    def get(self, timeout: float | None = None) -> T:
        """Extrae el elemento bloqueando hasta el timeout."""
        return self._q.get(timeout=timeout)

    def task_done(self) -> None:
        self._q.task_done()
