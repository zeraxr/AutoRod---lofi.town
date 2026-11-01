from typing import Protocol
from autorod.domain.models.image_payload import ImagePayload


class ITemplateRepository(Protocol):
    """Contrato de lectura para estados de juego fijos."""

    def load(self, ref_id: str) -> ImagePayload:
        """Extrae de memoria o binario y retorna el recurso visual puro."""
        ...