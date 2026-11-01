"""Utilidades de soporte para la interfaz Flet de AutoRod."""

from typing import Any
import flet as ft


def get_control_page(control: ft.Control | None) -> ft.Page | None:
    """
    Retorna la página a la que pertenece el control de forma 100% segura.
    En Flet 1.0+, acceder a control.page cuando no está en página lanza RuntimeError.
    Esta función intercepta la excepción y retorna None.
    """
    if control is None:
        return None
    try:
        return control.page
    except Exception:
        return None


def is_control_mounted(control: ft.Control | None) -> bool:
    """Verifica si un control está montado en una página activa sin lanzar RuntimeError."""
    return get_control_page(control) is not None


def safe_update(control: ft.Control | None) -> None:
    """Actualiza un control de Flet de forma segura, ignorando si aún no está montado en página."""
    if control is None:
        return
    try:
        page = get_control_page(control)
        if page is not None:
            control.update()
    except Exception:
        pass


def close_app_window(page: ft.Page | None) -> None:
    """
    Cierra la ventana nativa de Flet de forma asíncrona segura.
    En Flet 1.0+, page.window.destroy() es una corrutina async que debe ser
    planificada en el loop de eventos; de lo contrario produce RuntimeWarning
    y deja la interfaz en carga infinita.
    """
    if page is None or not hasattr(page, "window"):
        return

    async def _destroy_coro() -> None:
        try:
            await page.window.destroy()
        except Exception:
            pass

    try:
        fut = page.run_task(_destroy_coro)
        try:
            fut.result(timeout=0.8)
        except Exception:
            pass
    except Exception:
        pass
