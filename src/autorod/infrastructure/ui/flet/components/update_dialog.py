"""Ventana tipo 'hint' y diálogo oficial de comprobación y actualización de AutoRod."""

from __future__ import annotations

import webbrowser
import logging
import threading
from pathlib import Path
from typing import Callable, Any
import flet as ft

from autorod.infrastructure.ui.flet.theme import ThemeManager, ThemeTokens
from autorod.infrastructure.updater.github_checker import (
    UpdateInfo,
    check_for_updates,
    CURRENT_VERSION,
    REPO_SLUG
)
from autorod.infrastructure.updater.detector import detect_installation_type, InstallationType
from autorod.infrastructure.updater.downloader import UpdateDownloader
from autorod.infrastructure.ui.flet.utils import safe_update

logger = logging.getLogger(__name__)


class FletUpdateHintDialog:
    """
    Controlador de la ventana emergente tipo 'hint' con el estilo nativo de AutoRod (Tokyo Night):
    - Presenta feedback interactivo inmediato (Buscando, Al día, Nueva versión, Descarga en vivo).
    - Detecta automáticamente si la aplicación corre como versión Portable o Instalada por Setup.
    - Modo Portable: Notifica y proporciona acceso directo al repositorio oficial.
    - Modo Instalado: Descarga el último release y lanza la instalación asistida en caliente.
    """

    def __init__(
        self,
        page: ft.Page,
        theme_manager: ThemeManager | None = None,
        on_close_app: Callable[[], None] | None = None,
        on_update_status_changed: Callable[[bool], None] | None = None
    ) -> None:
        self.page = page
        self.theme_mgr = theme_manager or ThemeManager.get_instance()
        self.theme: ThemeTokens = self.theme_mgr.current
        self.on_close_app = on_close_app
        self.on_update_status_changed = on_update_status_changed

        self._downloader = UpdateDownloader()
        self._current_info: UpdateInfo | None = None
        self._is_checking = False
        self._download_dest_path: Path | None = None

        # Contenedores dinámicos de la interfaz
        self._body_column = ft.Column(spacing=14, horizontal_alignment=ft.CrossAxisAlignment.START)
        self._actions_row = ft.Row(alignment=ft.MainAxisAlignment.END, spacing=10)

        self._dialog_container = ft.Container(
            width=430,
            bgcolor="#0d0f17" if self.theme.mode == "dark" else "#ffffff",
            border=ft.Border.all(1, "#1b2233" if self.theme.mode == "dark" else "#e5e7eb"),
            border_radius=12,
            padding=ft.Padding.all(22),
            content=ft.Column(
                controls=[
                    self._create_header(),
                    ft.Divider(height=1, color="#1b2233" if self.theme.mode == "dark" else "#e5e7eb"),
                    self._body_column,
                    self._actions_row
                ],
                spacing=16,
                tight=True
            )
        )

        self.dialog = ft.AlertDialog(
            content=self._dialog_container,
            modal=False,
            bgcolor="#00000000",
            shape=ft.RoundedRectangleBorder(radius=12),
            content_padding=ft.Padding.all(0)
        )

    def _create_header(self) -> ft.Row:
        return ft.Row(
            controls=[
                ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.SYNC_ROUNDED, size=18, color="#38bdf8"),
                        ft.Text(
                            "Actualizaciones de AutoRod",
                            size=14,
                            weight=ft.FontWeight.W_600,
                            color="#ffffff" if self.theme.mode == "dark" else self.theme.text_primary
                        )
                    ],
                    spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER
                ),
                ft.IconButton(
                    icon=ft.Icons.CLOSE,
                    icon_size=16,
                    icon_color="#8f99b3",
                    tooltip="Cerrar",
                    on_click=lambda _: self.close(),
                    style=ft.ButtonStyle(padding=ft.Padding.all(4))
                )
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER
        )

    def show(self, preloaded_info: UpdateInfo | None = None) -> None:
        """Abre la ventana flotante tipo 'hint' y carga el estado pertinente."""
        if hasattr(self.page, "show_dialog"):
            try:
                self.page.show_dialog(self.dialog)
            except Exception:
                pass
        else:
            self.dialog.open = True
            self.page.update()

        if preloaded_info is not None:
            self._current_info = preloaded_info
            if preloaded_info.has_update:
                self._render_update_available(preloaded_info)
            else:
                self._render_up_to_date(preloaded_info.current_version)
        else:
            self.start_check()

    def close(self) -> None:
        """Cierra el diálogo de forma segura respetando Flet 1.0."""
        self._downloader.cancel()
        if hasattr(self.page, "pop_dialog"):
            try:
                self.page.pop_dialog()
            except Exception:
                pass
        else:
            self.dialog.open = False
            self.page.update()

    def start_check(self) -> None:
        """Inicia una comprobación asíncrona hacia GitHub."""
        if self._is_checking:
            return
        self._is_checking = True
        self._render_checking()

        def _worker() -> None:
            info = check_for_updates(current_version=CURRENT_VERSION)
            self._is_checking = False
            self._current_info = info

            if self.on_update_status_changed:
                self.on_update_status_changed(bool(info and info.has_update))

            if info is None:
                self._render_error("No se pudo conectar con los servidores de GitHub Releases.")
            elif info.has_update:
                self._render_update_available(info)
            else:
                self._render_up_to_date(info.current_version)

        t = threading.Thread(target=_worker, daemon=True, name="AutoRod-ManualUpdateCheck")
        t.start()

    def _render_checking(self) -> None:
        """Renderiza el estado de búsqueda activa."""
        self._body_column.controls = [
            ft.Row(
                controls=[
                    ft.ProgressRing(width=24, height=24, stroke_width=2.5, color="#38bdf8"),
                    ft.Column(
                        controls=[
                            ft.Text("Buscando actualizaciones...", size=13, weight=ft.FontWeight.W_500, color="#ffffff"),
                            ft.Text("Consultando últimos lanzamientos en GitHub", size=11, color="#8f99b3")
                        ],
                        spacing=2
                    )
                ],
                spacing=14,
                vertical_alignment=ft.CrossAxisAlignment.CENTER
            )
        ]
        self._actions_row.controls = [
            self._create_button("Cancelar", on_click=lambda _: self.close(), is_primary=False)
        ]
        safe_update(self._dialog_container)

    def _render_up_to_date(self, version: str) -> None:
        """Renderiza la confirmación de que el software se encuentra al día."""
        self._body_column.controls = [
            ft.Row(
                controls=[
                    ft.Icon(ft.Icons.CHECK_CIRCLE_ROUNDED, size=32, color="#10b981"),
                    ft.Column(
                        controls=[
                            ft.Text("¡AutoRod está actualizado!", size=15, weight=ft.FontWeight.W_600, color="#ffffff"),
                            ft.Text(f"Tienes la versión más reciente instalada (v{version}).", size=12, color="#a5b4ff")
                        ],
                        spacing=2
                    )
                ],
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER
            ),
            ft.Container(
                bgcolor="#141a2a",
                border=ft.Border.all(1, "#1b2233"),
                border_radius=8,
                padding=ft.Padding.symmetric(horizontal=12, vertical=10),
                content=ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.INFO_OUTLINE_ROUNDED, size=15, color="#8f99b3"),
                        ft.Text("Tu entorno cuenta con todas las optimizaciones de pesca al día.", size=11, color="#8f99b3")
                    ],
                    spacing=8
                )
            )
        ]
        self._actions_row.controls = [
            self._create_button("Comprobar de nuevo", on_click=lambda _: self.start_check(), is_primary=False, icon=ft.Icons.REFRESH_ROUNDED),
            self._create_button("Entendido", on_click=lambda _: self.close(), is_primary=True)
        ]
        safe_update(self._dialog_container)

    def _render_update_available(self, info: UpdateInfo) -> None:
        """
        Renderiza la vista de actualización disponible discriminando entre:
        - Versión Portable: Enlace y mensaje obligatorio para abrir el repositorio.
        - Versión Instalada: Botón de actualización directa con descarga automática.
        """
        install_type = detect_installation_type()
        is_portable = install_type in (InstallationType.PORTABLE, InstallationType.DEVELOPMENT)

        badge_color = "#38bdf8" if is_portable else "#10b981"
        badge_bg = "#0e1f38" if is_portable else "#0d231a"
        badge_text = "Versión Portable detectada" if is_portable else "Versión Instalada detectada"
        badge_icon = ft.Icons.FOLDER_ZIP_OUTLINED if is_portable else ft.Icons.SETTINGS_APPLICATIONS_OUTLINED

        version_banner = ft.Row(
            controls=[
                ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.ROCKET_LAUNCH_ROUNDED, size=20, color="#38bdf8"),
                        ft.Text(f"Nueva versión disponible: {info.latest_version}", size=14, weight=ft.FontWeight.W_600, color="#ffffff")
                    ],
                    spacing=8
                ),
                ft.Container(
                    bgcolor=badge_bg,
                    border=ft.Border.all(1, badge_color),
                    border_radius=6,
                    padding=ft.Padding.symmetric(horizontal=8, vertical=3),
                    content=ft.Row(
                        controls=[
                            ft.Icon(badge_icon, size=12, color=badge_color),
                            ft.Text(badge_text, size=10, weight=ft.FontWeight.W_500, color=badge_color)
                        ],
                        spacing=4
                    )
                )
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER
        )

        # Notas de la versión en caja deslizante sobria
        notes_box = ft.Container(
            bgcolor="#141a2a",
            border=ft.Border.all(1, "#1b2233"),
            border_radius=8,
            padding=ft.Padding.all(12),
            height=130,
            content=ft.ListView(
                controls=[
                    ft.Text(info.release_notes, size=11, color="#cbd5e1", selectable=True)
                ],
                spacing=4
            )
        )

        if is_portable:
            # Caso 1: Versión Portable -> Requisito explícito obligatorio
            instruction_text = ft.Text(
                "Se ha encontrado una nueva versión, haz click para abrir el repositorio",
                size=12,
                weight=ft.FontWeight.W_500,
                color="#ffffff"
            )
            action_btn = self._create_button(
                "Abrir Repositorio",
                on_click=lambda _: self._open_repository(info.html_url),
                is_primary=True,
                icon=ft.Icons.OPEN_IN_NEW_ROUNDED
            )
        else:
            # Caso 2: Versión Instalada por Setup -> Descarga directa e instalación automática
            instruction_text = ft.Text(
                "Se ha encontrado una nueva versión instalable. Haz clic para actualizar automáticamente.",
                size=12,
                weight=ft.FontWeight.W_500,
                color="#ffffff"
            )
            action_btn = self._create_button(
                "Actualizar Ahora",
                on_click=lambda _: self._start_auto_download(info),
                is_primary=True,
                icon=ft.Icons.DOWNLOAD_ROUNDED,
                accent_color=self.theme.primary
            )

        self._body_column.controls = [
            version_banner,
            notes_box,
            instruction_text
        ]
        self._actions_row.controls = [
            self._create_button("Cerrar", on_click=lambda _: self.close(), is_primary=False),
            action_btn
        ]
        safe_update(self._dialog_container)

    def _open_repository(self, url: str) -> None:
        """Abre el repositorio en el navegador web del sistema."""
        webbrowser.open(url)
        self.close()

    def _start_auto_download(self, info: UpdateInfo) -> None:
        """Inicia la descarga de la actualización con barra de progreso reactiva."""
        target_url = info.setup_download_url or info.download_url
        filename = info.asset_name if info.asset_name.endswith(".exe") else f"AutoRod-{info.latest_version}-Setup.exe"

        prog_bar = ft.ProgressBar(value=0.0, color=self.theme.primary, bgcolor="#141a2a", height=8, border_radius=4)
        status_text = ft.Text("Conectando con el servidor de descargas...", size=11, color="#a5b4ff")

        self._body_column.controls = [
            ft.Row(
                controls=[
                    ft.Icon(ft.Icons.DOWNLOAD_FOR_OFFLINE_ROUNDED, size=24, color="#10b981"),
                    ft.Column(
                        controls=[
                            ft.Text(f"Descargando AutoRod {info.latest_version}", size=14, weight=ft.FontWeight.W_600, color="#ffffff"),
                            status_text
                        ],
                        spacing=2
                    )
                ],
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER
            ),
            ft.Container(content=prog_bar, padding=ft.Padding.only(top=8, bottom=4))
        ]
        self._actions_row.controls = [
            self._create_button("Cancelar", on_click=lambda _: self._cancel_download(), is_primary=False)
        ]
        safe_update(self._dialog_container)

        def _on_progress(progress: float, downloaded: int, total: int) -> None:
            prog_bar.value = progress
            d_mb = downloaded / (1024 * 1024)
            t_mb = total / (1024 * 1024)
            status_text.value = f"Descargado: {d_mb:.1f} MB / {t_mb:.1f} MB ({int(progress * 100)}%)"
            safe_update(self._dialog_container)

        def _on_complete(dest_path: Path) -> None:
            self._download_dest_path = dest_path
            self._render_ready_to_install(dest_path)

        def _on_error(exc: Exception) -> None:
            self._render_error(f"Error durante la descarga: {exc}")

        self._downloader.download_installer(
            url=target_url,
            filename=filename,
            on_progress=_on_progress,
            on_complete=_on_complete,
            on_error=_on_error
        )

    def _cancel_download(self) -> None:
        self._downloader.cancel()
        self.close()

    def _render_ready_to_install(self, installer_path: Path) -> None:
        """Renderiza el estado de instalación finalizada y lista para ejecutar."""
        self._body_column.controls = [
            ft.Row(
                controls=[
                    ft.Icon(ft.Icons.TASK_ALT_ROUNDED, size=32, color="#10b981"),
                    ft.Column(
                        controls=[
                            ft.Text("¡Descarga completada!", size=15, weight=ft.FontWeight.W_600, color="#ffffff"),
                            ft.Text("El instalador se encuentra listo para actualizar AutoRod.", size=12, color="#cbd5e1")
                        ],
                        spacing=2
                    )
                ],
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER
            ),
            ft.Container(
                bgcolor="#0d231a",
                border=ft.Border.all(1, "#134e3a"),
                border_radius=8,
                padding=ft.Padding.all(12),
                content=ft.Text(
                    "Al hacer clic en 'Instalar y Reiniciar', AutoRod se cerrará ordenadamente "
                    "y se iniciará el asistente de instalación para aplicar los cambios.",
                    size=11,
                    color="#6ee7b7"
                )
            )
        ]
        self._actions_row.controls = [
            self._create_button("Cerrar", on_click=lambda _: self.close(), is_primary=False),
            self._create_button(
                "Instalar y Reiniciar",
                on_click=lambda _: self._launch_installer(installer_path),
                is_primary=True,
                accent_color=self.theme.primary,
                icon=ft.Icons.SYSTEM_UPDATE_ROUNDED
            )
        ]
        safe_update(self._dialog_container)

    def _launch_installer(self, path: Path) -> None:
        """Lanza el instalador y cierra la aplicación actual."""
        self.close()
        UpdateDownloader.launch_installer_and_exit(path, on_exit=self.on_close_app)

    def _render_error(self, message: str) -> None:
        """Renderiza el estado de error de conexión o descarga."""
        self._body_column.controls = [
            ft.Row(
                controls=[
                    ft.Icon(ft.Icons.WIFI_OFF_ROUNDED, size=28, color="#f59e0b"),
                    ft.Column(
                        controls=[
                            ft.Text("No se pudo comprobar la versión", size=14, weight=ft.FontWeight.W_600, color="#ffffff"),
                            ft.Text(message, size=11, color="#8f99b3")
                        ],
                        spacing=2
                    )
                ],
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER
            )
        ]
        self._actions_row.controls = [
            self._create_button("Cerrar", on_click=lambda _: self.close(), is_primary=False),
            self._create_button("Reintentar", on_click=lambda _: self.start_check(), is_primary=True, icon=ft.Icons.REFRESH_ROUNDED)
        ]
        safe_update(self._dialog_container)

    def _create_button(
        self,
        text: str,
        on_click: Callable[[Any], None],
        is_primary: bool = False,
        icon: Any = None,
        accent_color: str | None = None
    ) -> ft.Container:
        """Crea un botón estilizado según la paleta sobria de AutoRod."""
        color = accent_color or self.theme.primary
        bg = color if is_primary else "#141a2a"
        border = ft.Border.all(1, color if is_primary else "#1b2233")
        text_color = "#ffffff" if is_primary else "#cbd5e1"

        row_controls: list[ft.Control] = []
        if icon:
            row_controls.append(ft.Icon(icon, size=14, color=text_color))
        row_controls.append(ft.Text(text, size=12, weight=ft.FontWeight.W_500, color=text_color))

        return ft.Container(
            content=ft.Row(controls=row_controls, spacing=6, alignment=ft.MainAxisAlignment.CENTER),
            bgcolor=bg,
            border=border,
            border_radius=8,
            height=34,
            padding=ft.Padding.symmetric(horizontal=14),
            on_click=on_click,
            ink=True
        )
