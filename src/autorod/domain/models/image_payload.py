from dataclasses import dataclass
from enum import Enum


class PixelFormat(Enum):
    BGR8 = "BGR8"
    RGB8 = "RGB8"
    BGRA8 = "BGRA8"
    GRAY8 = "GRAY8"


@dataclass(frozen=True, slots=True, kw_only=True)
class ImagePayload:
    """
    Contenedor agnóstico e inmutable de datos binarios visuales.

    Attributes:
        width: Anchura en píxeles.
        height: Altura en píxeles.
        pixel_format: Estructura del color de cada píxel.
        stride: Tamaño de una fila completa en bytes (incluyendo padding).
        data: Buffer inmutable de solo lectura.
        frame_id: Identificador secuencial para observabilidad.
        captured_at_ns: Marca de tiempo desde reloj monotónico SOTA.
        source_id: Etiqueta de la fuente emisora (e.g., 'mss_main').
    """
    width: int
    height: int
    pixel_format: PixelFormat
    stride: int
    data: memoryview | bytes
    frame_id: int
    captured_at_ns: int
    source_id: str
    offset_x: int = 0
    offset_y: int = 0

    def __post_init__(self) -> None:
        """
        Valida las invariantes del fotograma y asegura inmutabilidad del buffer.

        Raises:
            ValueError: Si las dimensiones son inválidas o el buffer es corto.
        """
        if self.width <= 0 or self.height <= 0:
            raise ValueError("Las dimensiones deben ser positivas.")
        if self.stride <= 0:
            raise ValueError("El stride debe ser mayor a cero.")
        if len(self.data) < self.stride * self.height:
            raise ValueError("Longitud de datos inconsistente con stride * height.")
        if isinstance(self.data, memoryview) and not self.data.readonly:
            object.__setattr__(self, "data", self.data.toreadonly())

    def nbytes(self) -> int:
        """Calcula el tamaño del buffer en bytes."""
        return len(self.data)
