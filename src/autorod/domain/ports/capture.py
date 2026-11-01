from typing import Protocol
from autorod.domain.models.image_payload import ImagePayload


class ICaptureSource(Protocol):
    """Contrato del motor de ingesta de fotogramas del OS."""

    def start(self) -> None:
        """Inicializa el contexto subyacente. Puede lanzar CaptureError."""
        ...

    def stop(self) -> None:
        """Libera los punteros y manejadores de ventana asociados."""
        ...

    def grab(self) -> ImagePayload:
        """
        Captura sincrónicamente la pantalla.

        Returns:
            ImagePayload con el buffer copiado a memoria inmutable.
        """
        ...