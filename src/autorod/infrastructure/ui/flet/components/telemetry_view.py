"""Vista de Consola de Telemetría y Registros en Flet."""

import time
import flet as ft
from autorod.infrastructure.ui.flet.theme import ThemeManager
from autorod.infrastructure.ui.flet.utils import safe_update


class FletTelemetryView(ft.Container):
    """Consola moderna para streaming de registros de eventos en tiempo real."""

    def __init__(self, theme_manager: ThemeManager | None = None) -> None:
        self._theme_mgr = theme_manager or ThemeManager.get_instance()

        self._log_column = ft.Column(
            scroll=ft.ScrollMode.ADAPTIVE,
            spacing=3,
            auto_scroll=True
        )

        header = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("📊 Registro de Eventos y Telemetría", size=18, weight=ft.FontWeight.BOLD, color="#ffffff"),
                    ft.Text("Monitoreo en vivo de transiciones de estado, clics y pipeline de visión.", size=12, color="#9ca3af")
                ],
                spacing=3
            ),
            bgcolor="#11131c",
            border=ft.Border.all(1, "#1e2232"),
            border_radius=10,
            padding=ft.Padding.symmetric(horizontal=16, vertical=12)
        )

        console_box = ft.Container(
            content=self._log_column,
            bgcolor="#08090d",
            border=ft.Border.all(1, "#181a24"),
            border_radius=10,
            padding=ft.Padding.all(12),
            expand=True
        )

        super().__init__(
            content=ft.Column(
                controls=[
                    header,
                    console_box
                ],
                spacing=10,
                expand=True
            ),
            expand=True,
            padding=ft.Padding.all(14)
        )

        self.append_log("AutoRod inicializado con motor de interfaz Flet.")
        self.append_log("Pipeline Productor-Consumidor activo a 60 FPS.")

    def append_log(self, message: str) -> None:
        timestamp = time.strftime("%H:%M:%S")
        line = ft.Text(
            f"[{timestamp}] {message}",
            size=11,
            color="#3ecf8e",
            font_family="Consolas"
        )
        self._log_column.controls.append(line)
        if len(self._log_column.controls) > 300:
            self._log_column.controls.pop(0)

        safe_update(self)
