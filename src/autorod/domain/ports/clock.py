import threading
from typing import Protocol


class IClock(Protocol):
    """
    Abstracción de tiempos. Elimina `time.sleep` del proyecto y
    permite inyectar tiempos sintéticos durante los tests.
    """

    def monotonic_ns(self) -> int:
        """Devuelve nanosegundos desde reloj monotónico arbitrario."""
        ...

    def wait(self, timeout_s: float, cancel: threading.Event) -> bool:
        """
        Espera cooperativa.

        Returns:
            True si fue cancelada prematuramente, False si cumplió el timeout.
        """
        ...