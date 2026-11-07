"""Barra de título personalizada (Custom Titlebar) sin marco con controles nativos y botón de actualización."""

import webbrowser
from pathlib import Path
import flet as ft
from typing import Callable, Any
from autorod.infrastructure.ui.flet.theme import ThemeManager
from autorod.infrastructure.updater.github_checker import UpdateInfo
from autorod.infrastructure.ui.flet.utils import get_asset_path


class FletCustomTitleBar(ft.Container):
    """
    Barra de título personalizada superior (Frameless Window Titlebar).
    - Muestra el nombre oficial 'AutoRod' con el icono de la aplicación.
    - Área de arrastre fluida (WindowDragArea) con doble clic para maximizar/restaurar.
    - Botón de actualización prominente posicionado a la izquierda de los controles de ventana.
    - Botones nativos estilizados: Minimizar [-], Maximizar/Restaurar [□] y Cerrar [X].
    """

    def __init__(
        self,
        page: ft.Page | None,
        on_close: Callable[[], None],
        theme_manager: ThemeManager | None = None
    ) -> None:
        self._page_ref = page
        self._on_close = on_close
        self.theme_mgr = theme_manager or ThemeManager.get_instance()
        self._current_update_info: UpdateInfo | None = None

        # 1. Título y Logo Oficial con icono real del programa (sin emojis)
        logo_path = get_asset_path("icons/logo_32.png")
        if not logo_path.is_file():
            logo_path = get_asset_path("icons/logo.png")

        self._title_logo = ft.Image(
            src=str(logo_path),
            width=16,
            height=16,
            fit=ft.BoxFit.CONTAIN
        )

        self._title_text = ft.Text(
            "AutoRod",
            size=12,
            weight=ft.FontWeight.BOLD,
            color="#e4e4e7"
        )
        title_block = ft.Row(
            controls=[self._title_logo, self._title_text],
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.CENTER
        )

        # 2. Icono de Actualización SOTA con punto azul (Figma 1:1)
        self._update_dot = ft.Container(
            width=6,
            height=6,
            border_radius=3,
            bgcolor="#38bdf8",
            right=6,
            top=6,
            visible=True
        )
        self._update_sync_btn = ft.IconButton(
            icon=ft.Icons.SYNC_ROUNDED,
            icon_size=16,
            icon_color="#8f99b3",
            tooltip="Comprobar actualizaciones",
            on_click=self._show_update_dialog,
            style=ft.ButtonStyle(padding=ft.Padding.all(4))
        )
        self._update_button = ft.Stack(
            controls=[
                self._update_sync_btn,
                self._update_dot
            ],
            width=28,
            height=28
        )

        # 3. Botones de Control de Ventana (Estilo moderno Discord / VS Code)
        self._btn_minimize = self._create_window_button(
            icon=ft.Icons.REMOVE,
            tooltip="Minimizar",
            on_click=self._minimize_window
        )
        self._btn_maximize = self._create_window_button(
            icon=ft.Icons.CROP_SQUARE,
            tooltip="Maximizar",
            on_click=self._toggle_maximize_window
        )
        self._btn_close = self._create_window_button(
            icon=ft.Icons.CLOSE,
            tooltip="Cerrar AutoRod",
            on_click=lambda _: self._on_close(),
            is_close=True
        )

        window_controls_row = ft.Row(
            controls=[
                self._update_button,
                ft.Row(
                    controls=[
                        self._btn_minimize,
                        self._btn_maximize,
                        self._btn_close
                    ],
                    spacing=0
                )
            ],
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.CENTER
        )

        # 4. Área de Arrastre de Ventana (WindowDragArea)
        # Ocupa todo el espacio central para arrastrar y mover la ventana libremente
        drag_content = ft.Container(
            content=ft.Row(
                controls=[
                    title_block,
                    ft.Container(expand=True)  # Espacio flexible intermedio arrastrable
                ],
                alignment=ft.MainAxisAlignment.START,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                expand=True
            ),
            padding=ft.Padding.only(left=12),
            expand=True
        )

        draggable_header = ft.WindowDragArea(
            content=drag_content,
            expand=True
        )

        super().__init__(
            content=ft.Row(
                controls=[
                    draggable_header,
                    window_controls_row
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER
            ),
            bgcolor="#1a1b26",
            border=None,
            height=36,
            padding=ft.Padding.only(left=0, right=0, top=0, bottom=0)
        )

    def _create_window_button(
        self,
        icon: Any,
        tooltip: str,
        on_click: Callable[[Any], None],
        is_close: bool = False
    ) -> ft.Container:
        """Crea un botón de control de ventana interactivo con hover suave."""
        icon_ctrl = ft.Icon(icon, size=13, color="#94a3b8")

        def _on_hover(e: ft.HoverEvent) -> None:
            if e.data == "true":
                container.bgcolor = "#dc2626" if is_close else "#1e2230"
                icon_ctrl.color = "#ffffff"
            else:
                container.bgcolor = "transparent"
                icon_ctrl.color = "#94a3b8"
            container.update()

        container = ft.Container(
            content=icon_ctrl,
            width=44,
            height=36,
            alignment=ft.Alignment(0, 0),
            tooltip=tooltip,
            on_click=on_click,
            on_hover=_on_hover,
            bgcolor="transparent",
            animate=ft.Animation(150, ft.AnimationCurve.EASE_OUT)
        )
        return container

    def _get_page(self) -> ft.Page | None:
        """Obtiene la instancia de página activa."""
        try:
            return self.page or self._page_ref
        except Exception:
            return self._page_ref

    def _minimize_window(self, _: Any) -> None:
        """Minimiza la ventana al área de notificación de Windows."""
        p = self._get_page()
        if p and hasattr(p, "window"):
            p.window.minimized = True
            p.update()

    def _toggle_maximize_window(self, _: Any) -> None:
        """Alterna entre pantalla maximizada y tamaño normal."""
        p = self._get_page()
        if p and hasattr(p, "window"):
            p.window.maximized = not p.window.maximized
            p.update()

    def set_update_available(self, info: UpdateInfo) -> None:
        """Activa y hace visible el punto azul de actualización en el icono de sincronización."""
        self._current_update_info = info
        self._update_dot.visible = True
        self._update_dot.bgcolor = "#38bdf8"
        try:
            self._update_button.update()
        except Exception:
            pass

    def _show_update_dialog(self, _: Any) -> None:
        """Muestra el modal interactivo con los detalles de la nueva versión."""
        p = self._get_page()
        if not p or not self._current_update_info:
            return

        info = self._current_update_info

        def _open_download(_: Any) -> None:
            webbrowser.open(info.download_url)
            p.pop_dialog()

        def _close_dialog(_: Any) -> None:
            p.pop_dialog()

        dialog = ft.AlertDialog(
            title=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.ROCKET_LAUNCH, color="#10b981", size=22),
                    ft.Text(f"Nueva versión disponible: {info.latest_version}", size=15, weight=ft.FontWeight.BOLD)
                ],
                spacing=8
            ),
            content=ft.Column(
                controls=[
                    ft.Text(
                        f"Tu versión actual: v{info.current_version}\n"
                        f"Última versión oficial: {info.latest_version}",
                        size=12,
                        color="#94a3b8"
                    ),
                    ft.Divider(color="#27272a"),
                    ft.Text("Notas de la versión:", size=12, weight=ft.FontWeight.BOLD),
                    ft.Container(
                        content=ft.Text(
                            info.release_notes,
                            size=12,
                            color="#e4e4e7"
                        ),
                        max_height=180,
                        padding=8,
                        bgcolor="#12131a",
                        border_radius=6
                    )
                ],
                tight=True,
                spacing=8
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=_close_dialog),
                ft.ElevatedButton(
                    "Descargar Actualización",
                    icon=ft.Icons.DOWNLOAD,
                    bgcolor="#10b981",
                    color="#ffffff",
                    on_click=_open_download
                )
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        p.open_dialog(dialog)

    def apply_theme(self, tokens: ThemeTokens) -> None:
        self.bgcolor = tokens.shell_bg
        self._title_text.color = tokens.text_primary
        self._btn_minimize.icon_color = tokens.text_primary
        self._btn_maximize.icon_color = tokens.text_primary
        from autorod.infrastructure.ui.flet.utils import safe_update
        safe_update(self)
