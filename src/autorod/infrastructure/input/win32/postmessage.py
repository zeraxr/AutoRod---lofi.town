"""Simulador de entrada en segundo plano mediante Win32 PostMessageW.

Permite enviar eventos de ratón (movimiento virtual y clics) directamente a la
cola de mensajes de la ventana de destino (incluyendo navegadores Chromium)
sin mover el cursor físico del sistema ni interferir con el trabajo del usuario.
"""

import ctypes
from ctypes import wintypes
from collections.abc import Sequence
import logging
from typing import Any

from autorod.domain.ports.input_simulator import IInputSimulator
from autorod.domain.models.input_commands import (
    InputCommand,
    MouseClick,
    MouseMove,
    KeyPress,
    KeyRelease,
    MouseButton,
)

logger = logging.getLogger(__name__)

# Mensajes de ratón de Win32
WM_MOUSEMOVE = 0x0200
WM_LBUTTONDOWN = 0x0201
WM_LBUTTONUP = 0x0202
WM_RBUTTONDOWN = 0x0204
WM_RBUTTONUP = 0x0205
WM_MBUTTONDOWN = 0x0207
WM_MBUTTONUP = 0x0208

# Flags de wParam
MK_LBUTTON = 0x0001
MK_RBUTTON = 0x0002
MK_MBUTTON = 0x0010


class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


class RECT(ctypes.Structure):
    _fields_ = [
        ("left", ctypes.c_long),
        ("top", ctypes.c_long),
        ("right", ctypes.c_long),
        ("bottom", ctypes.c_long)
    ]


class Win32PostMessageSimulator(IInputSimulator):
    """
    Simulador Userland no intrusivo mediante Win32 PostMessageW.
    
    A diferencia de SendInput (modo legacy), este adaptador no altera la
    posición del puntero físico de Windows (GetCursorPos), permitiendo que
    el usuario continúe usando su ratón en su monitor primario sin interrupciones.
    
    Resuelve la jerarquía de ventanas de Chromium (Chrome_RenderWidgetHostHWND)
    y sincroniza el puntero virtual mediante WM_MOUSEMOVE previo a cada clic.
    """

    def __init__(self, user32: Any | None = None) -> None:
        if user32 is not None:
            self._user32 = user32
        else:
            self._user32 = ctypes.windll.user32
            self._setup_win32_signatures()

        self._last_x: int = 0
        self._last_y: int = 0
        self._last_hwnd: int | None = None

    def _setup_win32_signatures(self) -> None:
        """Configura los tipos de argumentos y retornos de las APIs Win32 para 64-bit."""
        try:
            self._user32.WindowFromPoint.argtypes = [POINT]
            self._user32.WindowFromPoint.restype = wintypes.HWND

            self._user32.ChildWindowFromPointEx.argtypes = [wintypes.HWND, POINT, wintypes.UINT]
            self._user32.ChildWindowFromPointEx.restype = wintypes.HWND

            self._user32.ScreenToClient.argtypes = [wintypes.HWND, ctypes.POINTER(POINT)]
            self._user32.ScreenToClient.restype = wintypes.BOOL

            self._user32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(RECT)]
            self._user32.GetWindowRect.restype = wintypes.BOOL

            self._user32.GetClassNameW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
            self._user32.GetClassNameW.restype = ctypes.c_int

            self._user32.IsWindowVisible.argtypes = [wintypes.HWND]
            self._user32.IsWindowVisible.restype = wintypes.BOOL

            self._user32.PostMessageW.argtypes = [
                wintypes.HWND,
                wintypes.UINT,
                wintypes.WPARAM,
                wintypes.LPARAM
            ]
            self._user32.PostMessageW.restype = wintypes.BOOL
        except Exception as exc:
            logger.debug("Error configurando firmas Win32: %s", exc)

    def _resolve_target_hwnd(self, screen_x: int, screen_y: int) -> int | None:
        """
        Encuentra la ventana de renderizado exacta en las coordenadas dadas.
        Inspecciona ventanas hijas para penetrar en contenedores de Chromium
        (como Chrome_RenderWidgetHostHWND) si están presentes.
        """
        try:
            pt = POINT(int(screen_x), int(screen_y))
            hwnd = self._user32.WindowFromPoint(pt)
            if not hwnd:
                return None

            deepest = [hwnd]

            def _enum_children(child_hwnd: int, _: int) -> bool:
                if self._user32.IsWindowVisible(child_hwnd):
                    rc = RECT()
                    self._user32.GetWindowRect(child_hwnd, ctypes.byref(rc))
                    if rc.left <= screen_x <= rc.right and rc.top <= screen_y <= rc.bottom:
                        cbuf = ctypes.create_unicode_buffer(256)
                        self._user32.GetClassNameW(child_hwnd, cbuf, 256)
                        cls_name = cbuf.value
                        if "Render" in cls_name or "Intermediate" in cls_name:
                            deepest[0] = child_hwnd
                            return False  # Encontrado render widget específico
                        deepest[0] = child_hwnd
                return True

            WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
            self._user32.EnumChildWindows(hwnd, WNDENUMPROC(_enum_children), 0)
            return deepest[0]
        except Exception as exc:
            logger.debug("Error resolviendo HWND objetivo en (%d, %d): %s", screen_x, screen_y, exc)
            return None

    def _make_lparam(self, x: int, y: int) -> int:
        """Empaqueta coordenadas X e Y en el formato lParam de Win32 (DWORD)."""
        return ((int(y) & 0xFFFF) << 16) | (int(x) & 0xFFFF)

    def _to_client_coords(self, hwnd: int, screen_x: int, screen_y: int) -> tuple[int, int]:
        """Traduce coordenadas globales de pantalla a coordenadas locales del área cliente."""
        pt = POINT(int(screen_x), int(screen_y))
        try:
            self._user32.ScreenToClient(hwnd, ctypes.byref(pt))
            return pt.x, pt.y
        except Exception:
            return screen_x, screen_y

    def execute(self, command: InputCommand) -> None:
        self.execute_batch([command])

    def execute_batch(self, commands: Sequence[InputCommand]) -> None:
        if not commands:
            return

        target_x = self._last_x
        target_y = self._last_y

        for cmd in commands:
            if isinstance(cmd, MouseMove):
                target_x = int(cmd.x)
                target_y = int(cmd.y)
                self._last_x = target_x
                self._last_y = target_y
                self._send_mouse_move(target_x, target_y)

            elif isinstance(cmd, MouseClick):
                self._send_mouse_click(target_x, target_y, cmd.button, cmd.pressed)

            elif isinstance(cmd, (KeyPress, KeyRelease)):
                # Reservado para comandos de teclado en segundo plano si se requiere
                pass

    def _send_mouse_move(self, screen_x: int, screen_y: int) -> None:
        """Envía WM_MOUSEMOVE para actualizar el puntero virtual de Chromium."""
        hwnd = self._resolve_target_hwnd(screen_x, screen_y)
        if not hwnd:
            return
        self._last_hwnd = hwnd
        cx, cy = self._to_client_coords(hwnd, screen_x, screen_y)
        lparam = self._make_lparam(cx, cy)
        self._user32.PostMessageW(hwnd, WM_MOUSEMOVE, 0, lparam)

    def _send_mouse_click(self, screen_x: int, screen_y: int, button: MouseButton, pressed: bool) -> None:
        """Inyecta el clic en la ventana de destino asegurando sincronización previa de puntero."""
        hwnd = self._resolve_target_hwnd(screen_x, screen_y)
        if not hwnd:
            hwnd = self._last_hwnd
        if not hwnd:
            return

        cx, cy = self._to_client_coords(hwnd, screen_x, screen_y)
        lparam = self._make_lparam(cx, cy)

        # 1. Asegurar sincronización del puntero virtual de Chromium en esa posición
        self._user32.PostMessageW(hwnd, WM_MOUSEMOVE, 0, lparam)

        # 2. Inyectar botón pulsado o liberado
        if button == MouseButton.LEFT:
            msg = WM_LBUTTONDOWN if pressed else WM_LBUTTONUP
            wparam = MK_LBUTTON if pressed else 0
        elif button == MouseButton.RIGHT:
            msg = WM_RBUTTONDOWN if pressed else WM_RBUTTONUP
            wparam = MK_RBUTTON if pressed else 0
        elif button == MouseButton.MIDDLE:
            msg = WM_MBUTTONDOWN if pressed else WM_MBUTTONUP
            wparam = MK_MBUTTON if pressed else 0
        else:
            msg = WM_LBUTTONDOWN if pressed else WM_LBUTTONUP
            wparam = MK_LBUTTON if pressed else 0

        self._user32.PostMessageW(hwnd, msg, wparam, lparam)

    def close(self) -> None:
        pass
