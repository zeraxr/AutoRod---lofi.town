"""Gestor de efectos nativos de ventana, transparencia e identidad de sistema en Windows.

Aplica de forma no bloqueante e industrial:
- Windows DWM Dark Mode (DwmSetWindowAttribute).
- Windows 11 Backdrop Styling (Acrylic / Mica).
- Transparencia y translucidez de ventana (alpha blending).
- Identidad de proceso Windows AppUserModelID y asignación de iconos de alta resolución.
"""

import os
import sys
import ctypes
import logging
from pathlib import Path
from typing import Any
import tkinter as tk

logger = logging.getLogger(__name__)

# Constantes de la API de Windows DWM
DWMWA_USE_IMMERSIVE_DARK_MODE_BEFORE_20H1 = 19
DWMWA_USE_IMMERSIVE_DARK_MODE = 20
DWMWA_SYSTEMBACKDROP_TYPE = 38
DWMWA_MICA_EFFECT = 1029

# Tipos de SystemBackdrop en Windows 11 Build 22621+
DWMSBT_AUTO = 0
DWMSBT_NONE = 1
DWMSBT_MAINWINDOW = 2      # Mica
DWMSBT_TRANSIENTWINDOW = 3 # Acrylic
DWMSBT_TABBEDWINDOW = 4    # Mica Alt


class WindowFXManager:
    """Administra la apariencia visual del contenedor nativo y la integración con el SO."""

    @staticmethod
    def setup_process_identity(app_id: str = "autorod.automation.visual.v2", window_title: str = "AutoRod") -> None:
        """Registra el proceso en Windows Shell para aislar el icono de la barra de tareas."""
        if sys.platform != "win32":
            return
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
            ctypes.windll.kernel32.SetConsoleTitleW(window_title)
        except Exception as exc:
            logger.debug("No se pudo configurar AppUserModelID: %s", exc)

    @staticmethod
    def apply_transparency(window: tk.Tk, opacity: float = 0.96) -> None:
        """
        Fija la opacidad de la ventana (0.0 a 1.0) para que calce con los colores
        del software y fondo de pantalla del usuario.
        """
        try:
            clamped = max(0.40, min(1.0, opacity))
            window.wm_attributes("-alpha", clamped)
        except Exception as exc:
            logger.debug("No se pudo aplicar transparencia de ventana: %s", exc)

    @staticmethod
    def apply_dark_mode_and_acrylic(window: tk.Tk, use_acrylic: bool = True) -> None:
        """Aplica modo oscuro inmersivo y efecto Acrylic / Mica vía Windows DWM."""
        if sys.platform != "win32":
            return

        window.update_idletasks()
        try:
            # Obtener HWND de la ventana Tkinter
            hwnd = ctypes.windll.user32.GetParent(window.winfo_id())
            if not hwnd:
                hwnd = window.winfo_id()

            # 1. Forzar Dark Mode en la barra de título nativa
            val = ctypes.c_int(1)
            # Probar atributo moderno (Windows 10 20H1+ y Windows 11)
            res = ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd,
                DWMWA_USE_IMMERSIVE_DARK_MODE,
                ctypes.byref(val),
                ctypes.sizeof(val)
            )
            if res != 0:
                # Probar atributo heredado para builds anteriores de Win10
                ctypes.windll.dwmapi.DwmSetWindowAttribute(
                    hwnd,
                    DWMWA_USE_IMMERSIVE_DARK_MODE_BEFORE_20H1,
                    ctypes.byref(val),
                    ctypes.sizeof(val)
                )

            # 2. Habilitar Backdrop Acrylic / Mica si está disponible (Windows 11)
            if use_acrylic:
                backdrop_type = ctypes.c_int(DWMSBT_TRANSIENTWINDOW)  # Acrylic suave
                ctypes.windll.dwmapi.DwmSetWindowAttribute(
                    hwnd,
                    DWMWA_SYSTEMBACKDROP_TYPE,
                    ctypes.byref(backdrop_type),
                    ctypes.sizeof(backdrop_type)
                )
        except Exception as exc:
            logger.debug("Efectos DWM no aplicables en este entorno: %s", exc)

    @staticmethod
    def load_and_set_icons(window: tk.Tk, assets_dir: Path | None = None) -> dict[str, Any]:
        """Carga y aplica los iconos oficiales a la ventana, barra de tareas y diálogos."""
        if assets_dir is None:
            assets_dir = Path(__file__).resolve().parents[3] / "assets" / "icons"

        icons: dict[str, Any] = {
            "ico": None,
            "logo_32": None,
            "logo_48": None
        }

        ico_path = assets_dir / "logo.ico"
        png_32_path = assets_dir / "logo_32.png"
        png_48_path = assets_dir / "logo_48.png"

        try:
            if ico_path.is_file():
                try:
                    window.iconbitmap(str(ico_path))
                    icons["ico"] = str(ico_path)
                except Exception:
                    pass

            if png_32_path.is_file():
                photo_32 = tk.PhotoImage(file=str(png_32_path))
                icons["logo_32"] = photo_32
                window.iconphoto(True, photo_32)

            if png_48_path.is_file():
                photo_48 = tk.PhotoImage(file=str(png_48_path))
                icons["logo_48"] = photo_48

        except Exception as exc:
            logger.warning("Error al cargar los iconos de la aplicación: %s", exc)

        return icons
