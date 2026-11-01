import ctypes
import threading
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
from autorod.infrastructure.input.translation import KEY_TO_SCANCODE

PUL = ctypes.POINTER(ctypes.c_ulong)

INPUT_MOUSE = 0
INPUT_KEYBOARD = 1

MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_MIDDLEDOWN = 0x0020
MOUSEEVENTF_MIDDLEUP = 0x0040
MOUSEEVENTF_ABSOLUTE = 0x8000

KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_SCANCODE = 0x0008


class MouseInput(ctypes.Structure):
    _fields_ = [
        ("dx", ctypes.c_long),
        ("dy", ctypes.c_long),
        ("mouseData", ctypes.c_ulong),
        ("dwFlags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("dwExtraInfo", PUL)
    ]


class KeyBdInput(ctypes.Structure):
    _fields_ = [
        ("wVk", ctypes.c_ushort),
        ("wScan", ctypes.c_ushort),
        ("dwFlags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("dwExtraInfo", PUL)
    ]


class HardwareInput(ctypes.Structure):
    _fields_ = [
        ("uMsg", ctypes.c_ulong),
        ("wParamL", ctypes.c_short),
        ("wParamH", ctypes.c_ushort)
    ]


class Input_I(ctypes.Union):
    _fields_ = [
        ("mi", MouseInput),
        ("ki", KeyBdInput),
        ("hi", HardwareInput)
    ]


class Input(ctypes.Structure):
    _fields_ = [
        ("type", ctypes.c_ulong),
        ("ii", Input_I)
    ]


class SendInputSimulator(IInputSimulator):
    """
    Implementación Userland concreta y completa usando user32.SendInput y SetCursorPos.
    Aísla las llamadas a ctypes, inyecta scan codes de hardware para evasión
    básica y rechaza totalmente librerías detectables como PyAutoGUI.
    """

    def __init__(
            self,
            click_hold_s: float = 0.050,
            cancel_event: threading.Event | None = None
    ) -> None:
        self._user32 = ctypes.windll.user32
        self._extra_info = ctypes.pointer(ctypes.c_ulong(0))
        self._click_hold_s = click_hold_s
        self._cancel_event = cancel_event or threading.Event()

    def _get_screen_metrics(self) -> tuple[int, int]:
        w = max(1, self._user32.GetSystemMetrics(0))
        h = max(1, self._user32.GetSystemMetrics(1))
        return w, h

    def execute(self, command: InputCommand) -> None:
        self.execute_batch([command])

    def execute_batch(self, commands: Sequence[InputCommand]) -> None:
        if not commands:
            return

        for i, cmd in enumerate(commands):
            if isinstance(cmd, MouseClick):
                flag = self._resolve_mouse_click_flag(cmd.button, cmd.pressed)
                mi = MouseInput(0, 0, 0, flag, 0, self._extra_info)
                inp = Input(type=INPUT_MOUSE, ii=Input_I(mi=mi))
                self._user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(Input))

                # Si acabamos de presionar y el siguiente comando es soltar el botón:
                # Mantenemos presionado click_hold_s (50 ms) para que el navegador y juego registren un clic físico real
                if cmd.pressed and self._click_hold_s > 0:
                    if i + 1 < len(commands) and isinstance(commands[i + 1], MouseClick) and not commands[i + 1].pressed:
                        self._cancel_event.wait(timeout=self._click_hold_s)

            elif isinstance(cmd, MouseMove):
                if cmd.absolute:
                    # Posicionamiento físico directo para precisión multimonitor y DPI
                    self._user32.SetCursorPos(int(cmd.x), int(cmd.y))
                else:
                    flags = MOUSEEVENTF_MOVE
                    mi = MouseInput(cmd.x, cmd.y, 0, flags, 0, self._extra_info)
                    inp = Input(type=INPUT_MOUSE, ii=Input_I(mi=mi))
                    self._user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(Input))

            elif isinstance(cmd, (KeyPress, KeyRelease)):
                scancode = KEY_TO_SCANCODE.get(cmd.code, 0)
                flags = KEYEVENTF_SCANCODE
                if isinstance(cmd, KeyRelease):
                    flags |= KEYEVENTF_KEYUP
                ki = KeyBdInput(0, scancode, flags, 0, self._extra_info)
                inp = Input(type=INPUT_KEYBOARD, ii=Input_I(ki=ki))
                self._user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(Input))

    def _resolve_mouse_click_flag(self, button: MouseButton, pressed: bool) -> int:
        if button == MouseButton.LEFT:
            return MOUSEEVENTF_LEFTDOWN if pressed else MOUSEEVENTF_LEFTUP
        elif button == MouseButton.RIGHT:
            return MOUSEEVENTF_RIGHTDOWN if pressed else MOUSEEVENTF_RIGHTUP
        elif button == MouseButton.MIDDLE:
            return MOUSEEVENTF_MIDDLEDOWN if pressed else MOUSEEVENTF_MIDDLEUP
        return MOUSEEVENTF_LEFTDOWN if pressed else MOUSEEVENTF_LEFTUP

    def close(self) -> None:
        pass
