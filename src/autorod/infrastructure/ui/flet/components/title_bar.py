"""Barra de título personalizada (Custom Titlebar) sin marco con controles nativos y botón de actualización."""

import webbrowser
import flet as ft
from typing import Callable, Any
from autorod.infrastructure.ui.flet.theme import ThemeManager
from autorod.infrastructure.updater.github_checker import UpdateInfo


class FletCustomTitleBar(ft.Container):
    """
    Barra de título personalizada superior (Frameless Window Titlebar).
    - Muestra el nombre oficial 'AutoRod' (sin 'v2.0').
    - Área de arrastre fluida (WindowDragArea) con doble clic para maximizar/restaurar.
    - Botón de actualización prominente posicionado a la izquierda de los controles de ventana.
    - Botones nativos estilizados: Minimizar [-], Maximizar/Restaurar [□] y Cerrar [✕].
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

        # 1. Título y Logo Oficial (Sin 'v2.0' según requerimiento de diseño)
        self._title_logo = ft.Text("🎣", size=14)
        self._title_text = ft.Text(
            "AutoRod",
            size=12,
            weight=ft.FontWeight.BOLD,
            color="#e2e8f0"
        )
        title_block = ft.Row(
            controls=[self._title_logo, self._title_text],
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.CENTER
        )

        # 2. Botón de Actualización (Ubicado a la izquierda de los botones de ventana)
        self._update_btn_text = ft.Text(
            "🚀 Actualización disponible",
            size=11,
            weight=ft.FontWeight.BOLD,
            color="#ffffff"
        )
        self._update_button = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.ROCKET_LAUNCH, size=13, color="#ffffff"),
                    self._update_btn_text
                ],
                spacing=6,
                alignment=ft.MainAxisAlignment.CENTER
            ),
            gradient=ft.LinearGradient(
                colors=["#10b981", "#059669"],
                begin=ft.Alignment(-1, 0),
                end=ft.Alignment(1, 0)
            ),
            border_radius=6,
            padding=ft.Padding.symmetric(horizontal=10, vertical=4),
            tooltip="¡Hay una nueva versión disponible! Haz clic para ver detalles",
            on_click=self._show_update_dialog,
            animate=ft.Animation(200, ft.AnimationCurve.EASE_OUT),
            visible=False  # Se activa automáticamente al detectar actualización
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
            spacing=10,
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
            bgcolor="#08090d",
            border=ft.Border.only(bottom=ft.BorderSide(1, "#181a24")),
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
        """Activa y hace visible el botón de actualización en la barra de título."""
        self._current_update_info = info
        self._update_btn_text.value = f"🚀 Actualizar ({info.latest_version})"
        self._update_button.visible = True
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
