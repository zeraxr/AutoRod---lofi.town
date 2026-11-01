import ctypes
from collections.abc import Sequence
from autorod.domain.ports.input_simulator import IInputSimulator
from autorod.domain.models.input_commands import (
    InputCommand,
    MouseClick,
    MouseMove,
    KeyPress,
    KeyRelease,
    MouseButton,
)
from autorod.domain.errors import InputBackendUnavailableError, ComponentClosedError
from autorod.infrastructure.input.translation import KEY_TO_SCANCODE

# Constantes oficiales de la API de Interception (Francisco Lopes)
INTERCEPTION_MOUSE_LEFT_BUTTON_DOWN = 0x001
INTERCEPTION_MOUSE_LEFT_BUTTON_UP = 0x002
INTERCEPTION_MOUSE_RIGHT_BUTTON_DOWN = 0x004
INTERCEPTION_MOUSE_RIGHT_BUTTON_UP = 0x008
INTERCEPTION_MOUSE_MIDDLE_BUTTON_DOWN = 0x010
INTERCEPTION_MOUSE_MIDDLE_BUTTON_UP = 0x020

INTERCEPTION_MOUSE_MOVE_RELATIVE = 0x000
INTERCEPTION_MOUSE_MOVE_ABSOLUTE = 0x001

INTERCEPTION_KEY_DOWN = 0x00
INTERCEPTION_KEY_UP = 0x01

# Dispositivos estándar por defecto
DEFAULT_KEYBOARD_DEVICE = 1
DEFAULT_MOUSE_DEVICE = 11


class InterceptionMouseStroke(ctypes.Structure):
    _fields_ = [
        ("state", ctypes.c_ushort),
        ("flags", ctypes.c_ushort),
        ("rolling", ctypes.c_short),
        ("x", ctypes.c_int),
        ("y", ctypes.c_int),
        ("information", ctypes.c_uint)
    ]


class InterceptionKeyStroke(ctypes.Structure):
    _fields_ = [
        ("code", ctypes.c_ushort),
        ("state", ctypes.c_ushort),
        ("information", ctypes.c_uint)
    ]


class InterceptionInputSimulator(IInputSimulator):
    """
    Implementación completa para el driver de Kernel Ring 0 (Interception API).
    Aísla las llamadas C vía ctypes, interactúa directamente con el driver de
    hardware evitando la inyección de la bandera LLMHF_INJECTED y eludiendo
    sistemas anti-cheat basados en ganchos (hooks) de Userland (Ring 3).
    """

    def __init__(
            self,
            dll_path: str = "interception.dll",
            keyboard_device: int = DEFAULT_KEYBOARD_DEVICE,
            mouse_device: int = DEFAULT_MOUSE_DEVICE
    ) -> None:
        self._keyboard_device = keyboard_device
        self._mouse_device = mouse_device
        self._context: ctypes.c_void_p | None = None

        try:
            self._dll = ctypes.cdll.LoadLibrary(dll_path)
        except (OSError, FileNotFoundError) as exc:
            raise InputBackendUnavailableError(
                f"Driver Interception Ring 0 no disponible: No se pudo cargar '{dll_path}'. "
                f"Asegúrese de tener instalado el driver en Windows y la DLL en el PATH."
            ) from exc

        self._init_prototypes()

        ctx = self._dll.interception_create_context()
        if not ctx:
            raise InputBackendUnavailableError(
                "interception_create_context() retornó NULL. "
                "Verifique que el servicio del driver de Interception esté activo."
            )
        self._context = ctx

    def _init_prototypes(self) -> None:
        self._dll.interception_create_context.restype = ctypes.c_void_p
        self._dll.interception_destroy_context.argtypes = [ctypes.c_void_p]
        self._dll.interception_destroy_context.restype = None
        self._dll.interception_send.argtypes = [
            ctypes.c_void_p,
            ctypes.c_int,
            ctypes.c_void_p,
            ctypes.c_uint
        ]
        self._dll.interception_send.restype = ctypes.c_int

    def execute(self, command: InputCommand) -> None:
        self.execute_batch([command])

    def execute_batch(self, commands: Sequence[InputCommand]) -> None:
        if self._context is None:
            raise ComponentClosedError("InterceptionInputSimulator ya fue cerrado o no está inicializado.")

        for cmd in commands:
            if isinstance(cmd, MouseClick):
                state = self._resolve_mouse_state(cmd.button, cmd.pressed)
                stroke = InterceptionMouseStroke(
                    state=state,
                    flags=0,
                    rolling=0,
                    x=0,
                    y=0,
                    information=0
                )
                self._dll.interception_send(
                    self._context,
                    self._mouse_device,
                    ctypes.byref(stroke),
                    1
                )

            elif isinstance(cmd, MouseMove):
                flags = INTERCEPTION_MOUSE_MOVE_ABSOLUTE if cmd.absolute else INTERCEPTION_MOUSE_MOVE_RELATIVE
                stroke = InterceptionMouseStroke(
                    state=0,
                    flags=flags,
                    rolling=0,
                    x=cmd.x,
                    y=cmd.y,
                    information=0
                )
                self._dll.interception_send(
                    self._context,
                    self._mouse_device,
                    ctypes.byref(stroke),
                    1
                )

            elif isinstance(cmd, (KeyPress, KeyRelease)):
                scancode = KEY_TO_SCANCODE.get(cmd.code, 0)
                state = INTERCEPTION_KEY_DOWN if isinstance(cmd, KeyPress) else INTERCEPTION_KEY_UP
                stroke = InterceptionKeyStroke(
                    code=scancode,
                    state=state,
                    information=0
                )
                self._dll.interception_send(
                    self._context,
                    self._keyboard_device,
                    ctypes.byref(stroke),
                    1
                )

    def _resolve_mouse_state(self, button: MouseButton, pressed: bool) -> int:
        if button == MouseButton.LEFT:
            return INTERCEPTION_MOUSE_LEFT_BUTTON_DOWN if pressed else INTERCEPTION_MOUSE_LEFT_BUTTON_UP
        elif button == MouseButton.RIGHT:
            return INTERCEPTION_MOUSE_RIGHT_BUTTON_DOWN if pressed else INTERCEPTION_MOUSE_RIGHT_BUTTON_UP
        elif button == MouseButton.MIDDLE:
            return INTERCEPTION_MOUSE_MIDDLE_BUTTON_DOWN if pressed else INTERCEPTION_MOUSE_MIDDLE_BUTTON_UP
        return INTERCEPTION_MOUSE_LEFT_BUTTON_DOWN if pressed else INTERCEPTION_MOUSE_LEFT_BUTTON_UP

    def close(self) -> None:
        """Libera de forma estricta el contexto del driver Interception."""
        if self._context is not None:
            try:
                self._dll.interception_destroy_context(self._context)
            finally:
                self._context = None
