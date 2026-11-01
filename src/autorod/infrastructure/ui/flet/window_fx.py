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

    @staticmethod
    def configure_window(page: ft.Page, title: str = "AutoRod", opacity: float = 0.96) -> None:
        """Configura las dimensiones, modo oscuro, opacidad e iconos de la ventana Flet."""
        page.title = title
        page.bgcolor = "#090a0f"
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
            page.window.bgcolor = "#090a0f"
            page.window.opacity = max(0.40, min(1.0, opacity))

            # Icono
            icons_dir = Path(__file__).resolve().parents[3] / "assets" / "icons"
            ico_path = icons_dir / "logo.ico"
            png_path = icons_dir / "logo_32.png"

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
