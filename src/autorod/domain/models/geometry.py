from dataclasses import dataclass


@dataclass(frozen=True, slots=True, kw_only=True)
class Point:
    """Coordenada matemática pura en un plano 2D."""
    x: int
    y: int


@dataclass(frozen=True, slots=True, kw_only=True)
class Size:
    """Dimensiones 2D."""
    width: int
    height: int

    def __post_init__(self) -> None:
        if self.width < 0 or self.height < 0:
            raise ValueError("Dimensiones no pueden ser negativas.")


@dataclass(frozen=True, slots=True, kw_only=True)
class Region:
    """Rectángulo delimitador agnóstico."""
    top_left: Point
    size: Size