"""Integración nativa con Windows Shell y efectos de ventana para Flet."""

import sys
import ctypes
import logging
from pathlib import Path
import flet as ft

logger = logging.getLogger(__name__)

DWMWA_USE_IMMERSIVE_DARK_MODE_BEFORE_20H1 = 19
DWMWA_USE_IMMERSIVE_DARK_MODE = 20
DWMWA_SYSTEMBACKDROP_TYPE = 38
DWMSBT_TRANSIENTWINDOW = 3  # Acrylic


class FletWindowFX:
    """Administra la identidad del proceso en Windows Shell y efectos DWM en Flet."""

    @staticmethod
    def setup_process_identity(app_id: str = "autorod.automation", title: str = "AutoRod") -> None:
        """Registra el proceso para asegurar icono oficial e independencia en Task Manager."""
        if sys.platform != "win32":
            return
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
            ctypes.windll.kernel32.SetConsoleTitleW(title)
        except Exception as exc:
            logger.debug("No se pudo configurar AppUserModelID: %s", exc)

        # Activar ejecución en segundo plano y alta precisión de temporizadores
        FletWindowFX.enable_background_execution()

    @staticmethod
    def enable_background_execution() -> None:
        """
        Garantiza que AutoRod y el runtime de Flutter continúen ejecutándose
        a máximo rendimiento (60 FPS / 1ms timer precision) sin throttling ni
        suspensión cuando la ventana pierde el foco o el usuario navega en otra app.
        """
        if sys.platform != "win32":
            return

        try:
            # 1. Fijar resolución de temporizadores del sistema a 1ms
            ctypes.windll.winmm.timeBeginPeriod(1)
        except Exception as exc:
            logger.debug("No se pudo configurar timeBeginPeriod(1): %s", exc)

        try:
            # 2. Prevenir suspensión por inactividad del sistema operativo
            # ES_CONTINUOUS (0x80000000) | ES_SYSTEM_REQUIRED (0x00000001)
            from ctypes import wintypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetThreadExecutionState.argtypes = [wintypes.DWORD]
            kernel32.SetThreadExecutionState.restype = wintypes.DWORD
            kernel32.SetThreadExecutionState(0x80000000 | 0x00000001)
        except Exception as exc:
            logger.debug("No se pudo configurar SetThreadExecutionState: %s", exc)

        try:
            # 3. Prioridad ABOVE_NORMAL para el proceso actual
            from ctypes import wintypes
            kernel32 = ctypes.windll.kernel32
            kernel32.GetCurrentProcess.restype = wintypes.HANDLE
            kernel32.SetPriorityClass.argtypes = [wintypes.HANDLE, wintypes.DWORD]
            kernel32.SetPriorityClass.restype = wintypes.BOOL
            h_proc = kernel32.GetCurrentProcess()
            kernel32.SetPriorityClass(h_proc, 0x00008000)
        except Exception as exc:
            logger.debug("No se pudo elevar prioridad del proceso: %s", exc)

        try:
            # 4. Desactivar EcoQoS / Power Throttling en Windows 11 (22H2+)
            from ctypes import wintypes
            kernel32 = ctypes.windll.kernel32
            kernel32.GetCurrentProcess.restype = wintypes.HANDLE

            class PROCESS_POWER_THROTTLING_STATE(ctypes.Structure):
                _fields_ = [
                    ("Version", wintypes.DWORD),
                    ("ControlMask", wintypes.DWORD),
                    ("StateMask", wintypes.DWORD),
                ]

            state = PROCESS_POWER_THROTTLING_STATE(1, 1, 0)
            kernel32.SetProcessInformation.argtypes = [
                wintypes.HANDLE,
                wintypes.DWORD,
                wintypes.LPVOID,
                wintypes.DWORD
            ]
            kernel32.SetProcessInformation.restype = wintypes.BOOL
            kernel32.SetProcessInformation(
                kernel32.GetCurrentProcess(),
                4,
                ctypes.byref(state),
                ctypes.sizeof(state)
            )
        except Exception as exc:
            logger.debug("No se pudo desactivar Power Throttling (EcoQoS): %s", exc)

        # 5. Optimizar procesos secundarios (flet.exe / runtime de Flutter)
        FletWindowFX.optimize_child_processes()

    @staticmethod
    def optimize_child_processes() -> None:
        """Eleva la prioridad de los procesos secundarios como flet.exe para evitar throttled frames."""
        if sys.platform != "win32":
            return
        try:
            import os
            from ctypes import wintypes
            kernel32 = ctypes.windll.kernel32
            TH32CS_SNAPPROCESS = 0x00000002
            PROCESS_SET_INFORMATION = 0x0200
            ABOVE_NORMAL_PRIORITY_CLASS = 0x00008000

            class PROCESSENTRY32(ctypes.Structure):
                _fields_ = [
                    ("dwSize", wintypes.DWORD),
                    ("cntUsage", wintypes.DWORD),
                    ("th32ProcessID", wintypes.DWORD),
                    ("th32DefaultHeapID", ctypes.POINTER(wintypes.ULONG)),
                    ("th32ModuleID", wintypes.DWORD),
                    ("cntThreads", wintypes.DWORD),
                    ("th32ParentProcessID", wintypes.DWORD),
                    ("pcPriClassBase", wintypes.LONG),
                    ("dwFlags", wintypes.DWORD),
                    ("szExeFile", ctypes.c_char * 260)
                ]

            current_pid = os.getpid()
            h_snap = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
            if h_snap == -1 or h_snap == 0xFFFFFFFFFFFFFFFF:
                return

            pe = PROCESSENTRY32()
            pe.dwSize = ctypes.sizeof(PROCESSENTRY32)

            if kernel32.Process32First(h_snap, ctypes.byref(pe)):
                while True:
                    if pe.th32ParentProcessID == current_pid:
                        child_pid = pe.th32ProcessID
                        h_proc = kernel32.OpenProcess(PROCESS_SET_INFORMATION, False, child_pid)
                        if h_proc:
                            kernel32.SetPriorityClass(h_proc, ABOVE_NORMAL_PRIORITY_CLASS)
                            kernel32.CloseHandle(h_proc)
                    if not kernel32.Process32Next(h_snap, ctypes.byref(pe)):
                        break

            kernel32.CloseHandle(h_snap)
        except Exception as exc:
            logger.debug("Error optimizando procesos secundarios: %s", exc)

    @staticmethod
    def restore_process_timers() -> None:
        """Restaura la resolución por defecto de temporizadores al cerrar la app."""
        if sys.platform != "win32":
            return
        try:
            ctypes.windll.winmm.timeEndPeriod(1)
        except Exception:
            pass

    @staticmethod
    def configure_window(page: ft.Page, title: str = "AutoRod", opacity: float = 1.0) -> None:
        """Configura las dimensiones, modo oscuro, opacidad sólida e iconos de la ventana Flet."""
        page.title = title
        page.bgcolor = "#070709"
        page.theme_mode = ft.ThemeMode.DARK
        page.padding = 0
        page.spacing = 0

        # Configuración de Window en Flet
        if hasattr(page, "window"):
            page.window.title = title
            page.window.width = 1060
            page.window.height = 720
            page.window.min_width = 860
            page.window.min_height = 600
            page.window.always_on_top = True
            page.window.bgcolor = "#070709"
            page.window.opacity = max(0.40, min(1.0, opacity))
            page.window.title_bar_hidden = True

            # Icono nativo
            from autorod.infrastructure.ui.flet.utils import get_asset_path
            ico_path = get_asset_path("icons/logo.ico")
            png_path = get_asset_path("icons/logo_32.png")

            if ico_path.is_file():
                page.window.icon = str(ico_path)
            elif png_path.is_file():
                page.window.icon = str(png_path)

    @staticmethod
    def apply_transparency(page: ft.Page, opacity: float) -> None:
        """Ajusta dinámicamente la opacidad/transparencia de la ventana."""
        if hasattr(page, "window"):
            try:
                page.window.opacity = max(0.40, min(1.0, opacity))
                page.update()
            except Exception as exc:
                logger.debug("Error al aplicar transparencia en Flet: %s", exc)
