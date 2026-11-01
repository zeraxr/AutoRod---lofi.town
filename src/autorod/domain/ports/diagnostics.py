from typing import Protocol
from autorod.domain.models.diagnostics import DiagnosticFrame


class IDiagnosticsSink(Protocol):
    """
    Sumidero no bloqueante que conecta el dominio asíncrono con Tkinter.
    """

    def publish(self, frame: DiagnosticFrame) -> None:
        """
        Inserta el diagnóstico con política documentada de descarte de más antiguos.
        Nunca toca APIs gráficas directamente y es hilo-seguro.
        """
        ...


class IDiagnosticsRenderer(Protocol):
    """
    Transfiere Diagnósticos a una superficie gráfica/matriz concreta.
    """

    def render(self, frame: DiagnosticFrame) -> bytes | memoryview:
        """Genera datos listos para consumir en un PhotoImage de UI."""
        ...