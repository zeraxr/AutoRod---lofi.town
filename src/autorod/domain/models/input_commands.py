from dataclasses import dataclass
from enum import Enum


class MouseButton(Enum):
    LEFT = "LEFT"
    RIGHT = "RIGHT"
    MIDDLE = "MIDDLE"


class KeyCode(Enum):
    """Mapeado abstracto de teclas. En infraestructura se traducirá a Scan Codes."""
    SPACE = "SPACE"
    ENTER = "ENTER"
    Q = "Q"
    # Añadir más según necesidad...


@dataclass(frozen=True, slots=True, kw_only=True)
class InputCommand:
    """Base agnóstica para comandos de inyección."""
    pass


@dataclass(frozen=True, slots=True, kw_only=True)
class MouseMove(InputCommand):
    x: int
    y: int
    absolute: bool = True


@dataclass(frozen=True, slots=True, kw_only=True)
class MouseClick(InputCommand):
    button: MouseButton
    pressed: bool


@dataclass(frozen=True, slots=True, kw_only=True)
class KeyPress(InputCommand):
    code: KeyCode


@dataclass(frozen=True, slots=True, kw_only=True)
class KeyRelease(InputCommand):
    code: KeyCode