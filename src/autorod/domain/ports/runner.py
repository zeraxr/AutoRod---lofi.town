from typing import Protocol


class IPipelineRunner(Protocol):
    """
    Contrato superior de ejecución del bucle Productor-Consumidor.
    """

    def start(self) -> None:
        """Despliega hilos y colas; sin bloquear."""
        ...

    def stop(self) -> None:
        """Inyecta centinelas y apaga cooperativamente."""
        ...

    def join(self, timeout_s: float | None = None) -> None:
        """Espera activa hasta que todo el grafo colapse ordenadamente."""
        ...