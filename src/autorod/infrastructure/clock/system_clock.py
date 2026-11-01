import time
import threading
from autorod.domain.ports.clock import IClock


class SystemClock(IClock):
    """Implementación del reloj basada en el sistema operativo."""

    def monotonic_ns(self) -> int:
        return time.monotonic_ns()

    def wait(self, timeout_s: float, cancel: threading.Event) -> bool:
        """
        Bloquea cooperativamente hasta el timeout o hasta que se dispare el evento.
        Espera cooperativa e interrumpible en nanosegundos.
        """
        return cancel.wait(timeout=timeout_s)
