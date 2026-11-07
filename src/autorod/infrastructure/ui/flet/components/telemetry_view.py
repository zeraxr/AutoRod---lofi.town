"""Vista de Consola de Telemetría y Registros en Flet con Diseño Unificado (Figma 1:1)."""

import time
from typing import Any
import flet as ft
from autorod.infrastructure.ui.flet.theme import ThemeManager, ThemeTokens
from autorod.infrastructure.ui.flet.utils import safe_update


class FletTelemetryView(ft.Container):
    """Consola moderna para streaming de registros de eventos en tiempo real con diseño unificado estilo Figma."""

    def __init__(self, theme_manager: ThemeManager | None = None) -> None:
        self._theme_mgr = theme_manager or ThemeManager.get_instance()
        self._tokens: ThemeTokens = self._theme_mgr.current
        self._start_time = time.time()

        self._log_column = ft.Column(
            scroll=ft.ScrollMode.ADAPTIVE,
            spacing=4,
            auto_scroll=True
        )

        # ---------------------------------------------------------------------
        # 0. HEADER PRINCIPAL (Figma 72:4730)
        # ---------------------------------------------------------------------
        self._title_text = ft.Text(
            "Telemetría",
            size=29,
            weight=ft.FontWeight.W_600,
            color="#ffffff" if self._tokens.mode == "dark" else self._tokens.text_primary
        )
        self._subtitle_text = ft.Text(
            "Acciones del programa AutoRod en tiempo real.",
            size=13,
            weight=ft.FontWeight.NORMAL,
            color="#a5b4ff" if self._tokens.mode == "dark" else self._tokens.text_secondary
        )

        self._status_dot = ft.Container(width=5, height=5, border_radius=3, bgcolor="#5554d9")
        self._status_label = ft.Text("Pausado", size=10, color="#a5b4ff")
        self._status_badge = ft.Container(
            content=ft.Row(
                controls=[
                    self._status_dot,
                    self._status_label
                ],
                spacing=6,
                alignment=ft.MainAxisAlignment.CENTER
            ),
            bgcolor="#141a2a" if self._tokens.mode == "dark" else "#ffffff",
            border=ft.Border.all(1, "#1b2233" if self._tokens.mode == "dark" else "#e5e7eb"),
            border_radius=6,
            padding=ft.Padding.symmetric(horizontal=9, vertical=5)
        )

        self._clear_btn = ft.Container(visible=False)

        header = ft.Row(
            controls=[
                ft.Column(
                    controls=[self._title_text, self._subtitle_text],
                    spacing=8
                ),
                self._status_badge
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER
        )

        # ---------------------------------------------------------------------
        # 1. CONSOLA DE ACCIONES (Figma 72:4822)
        # ---------------------------------------------------------------------
        self._filter_dropdown = ft.Dropdown(
            options=[
                ft.DropdownOption("5m", "Últimos 5 minutos"),
                ft.DropdownOption("15m", "Últimos 15 minutos"),
                ft.DropdownOption("all", "Toda la sesión")
            ],
            value="5m",
            bgcolor="#141a2a" if self._tokens.mode == "dark" else "#ffffff",
            border_color="#2a2f3a" if self._tokens.mode == "dark" else "#e5e7eb",
            focused_border_color=self._tokens.primary,
            text_size=12,
            content_padding=ft.Padding.symmetric(horizontal=12, vertical=8),
            width=165,
            height=34
        )

        console_header_row = ft.Row(
            controls=[
                ft.Column(
                    controls=[
                        ft.Text("Consola de acciones", size=14, weight=ft.FontWeight.W_600, color="#ffffff" if self._tokens.mode == "dark" else self._tokens.text_primary),
                        ft.Text("Secuencia de operaciones ejecutadas por AutoRod durante la sesión.", size=11, color="#8f99b3")
                    ],
                    spacing=5
                ),
                self._filter_dropdown
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER
        )

        info_line = ft.Row(
            controls=[
                ft.Icon(ft.Icons.INFO_OUTLINE_ROUNDED, size=13, color="#8f99b3"),
                ft.Text("La consola muestra la secuencia de acciones ejecutadas por AutoRod durante la sesión.", size=11, color="#8f99b3")
            ],
            spacing=8
        )

        self._console_card_frame = ft.Container(
            content=ft.Column(
                controls=[
                    console_header_row,
                    ft.Container(
                        content=self._log_column,
                        expand=True,
                        padding=ft.Padding.symmetric(vertical=4)
                    ),
                    info_line
                ],
                spacing=12,
                expand=True
            ),
            bgcolor="#0d0f17" if self._tokens.mode == "dark" else "#ffffff",
            border=ft.Border.all(1, "#1b2233" if self._tokens.mode == "dark" else "#e5e7eb"),
            border_radius=12,
            padding=ft.Padding.all(16),
            expand=True
        )

        # ---------------------------------------------------------------------
        # 2. ACCIONES DEL REGISTRO (Figma 72:4882)
        # ---------------------------------------------------------------------
        self._export_btn = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.DOWNLOAD_ROUNDED, size=14, color="#ffffff"),
                    ft.Text("Exportar registro", size=12, color="#ffffff", weight=ft.FontWeight.NORMAL)
                ],
                spacing=8,
                alignment=ft.MainAxisAlignment.CENTER
            ),
            bgcolor="#141a2a" if self._tokens.mode == "dark" else "#ffffff",
            border=ft.Border.all(1, "#2a2f3a" if self._tokens.mode == "dark" else "#e5e7eb"),
            border_radius=8,
            height=36,
            padding=ft.Padding.symmetric(horizontal=13),
            on_click=lambda _: self._export_logs(),
            ink=True
        )

        footer_row = ft.Row(
            controls=[
                ft.Text("Los datos se guardan solo en este equipo.", size=11, color="#8f99b3"),
                self._export_btn
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER
        )

        # Campos de compatibilidad de métricas
        self._val_session = ft.Text("00:00:00", visible=False)
        self._val_latency = ft.Text("0 ms", visible=False)
        self._val_success = ft.Text("0", visible=False)
        self._val_alerts = ft.Text("0", visible=False)

        super().__init__(
            content=ft.Column(
                controls=[
                    header,
                    self._console_card_frame,
                    footer_row,
                    self._val_session,
                    self._val_latency,
                    self._val_success,
                    self._val_alerts
                ],
                spacing=16,
                expand=True
            ),
            expand=True,
            bgcolor=self._tokens.canvas_bg,
            padding=ft.Padding.only(left=32, right=32, top=48, bottom=28),
            border_radius=ft.BorderRadius.only(top_left=16, bottom_left=16)
        )

        self.append_log("AutoRod inicializado con arquitectura Clean Architecture SOTA.")
        self.append_log("Pipeline Productor-Consumidor activo a 60 FPS.")

    def clear_logs(self, e: Any = None) -> None:
        """Limpia todos los registros visuales acumulados en la consola."""
        self._log_column.controls.clear()
        self.append_log("Consola reiniciada por el usuario.")
        safe_update(self)

    def append_log(self, message: str, tag: str = "Evento", subtext: str = "") -> None:
        timestamp = time.strftime("%H:%M:%S")
        is_dark = self._tokens.mode == "dark"
        text_color = "#ffffff" if is_dark else self._tokens.text_primary

        tag_val = tag
        msg_lower = message.lower()
        if "pausa" in msg_lower:
            tag_val = "Pausa"
        elif "completad" in msg_lower or "acierto" in msg_lower or "éxito" in msg_lower:
            tag_val = "Correcto"
        elif "detect" in msg_lower or "objetivo" in msg_lower:
            tag_val = "Detección"
        elif "captura" in msg_lower:
            tag_val = "Captura"
        elif "iniciad" in msg_lower or "inicio" in msg_lower:
            tag_val = "Inicio"
        elif "configur" in msg_lower:
            tag_val = "Configuración"

        entry = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Text(timestamp, size=11, color="#8f99b3", width=72),
                    ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Text(tag_val, size=10, color="#a5b4ff"),
                                    ft.Text(message, size=12, color=text_color, expand=True)
                                ],
                                spacing=8
                            ),
                            ft.Text(subtext, size=11, color="#8f99b3") if subtext else ft.Container(height=0)
                        ],
                        spacing=2,
                        expand=True
                    )
                ],
                spacing=12,
                alignment=ft.MainAxisAlignment.START,
                vertical_alignment=ft.CrossAxisAlignment.START
            ),
            padding=ft.Padding.symmetric(vertical=4)
        )
        setattr(entry, "value", f"[{timestamp}] {message}")
        self._log_column.controls.append(entry)
        if len(self._log_column.controls) > 300:
            self._log_column.controls.pop(0)

        safe_update(self)

    def _export_logs(self) -> None:
        try:
            import os
            os.makedirs("logs", exist_ok=True)
            with open("logs/telemetry_export.log", "w", encoding="utf-8") as f:
                f.write(f"=== AutoRod Telemetry Export ({time.strftime('%Y-%m-%d %H:%M:%S')}) ===\n")
                f.write(f"Eventos registrados: {len(self._log_column.controls)}\n")
        except Exception:
            pass

    def update_metrics(self, session_str: str, latency_ms: float, catches: int, alerts: int) -> None:
        self._val_session.value = session_str
        self._val_latency.value = f"{latency_ms:.1f} ms"
        self._val_success.value = str(catches)
        self._val_alerts.value = str(alerts)
        safe_update(self)

    def set_bot_running(self, running: bool) -> None:
        """Actualiza el indicador de estado reactivo superior en tiempo real."""
        if running:
            self._status_dot.bgcolor = "#10b981"
            self._status_label.value = "Activo"
            self._status_label.color = "#10b981"
        else:
            self._status_dot.bgcolor = "#5554d9"
            self._status_label.value = "Pausado"
            self._status_label.color = "#a5b4ff"
        safe_update(self._status_badge)

    def apply_theme(self, tokens: ThemeTokens) -> None:
        self._tokens = tokens
        self.bgcolor = tokens.canvas_bg
        self._title_text.color = tokens.text_primary
        self._subtitle_text.color = tokens.text_secondary
        self._val_session.color = tokens.primary
        self._val_latency.color = tokens.primary
        self._val_success.color = tokens.primary
        self._val_alerts.color = tokens.primary
        self._clear_btn.bgcolor = tokens.sub_bg
        self._clear_btn.border = ft.Border.all(1, tokens.card_border)
        self._status_badge.bgcolor = tokens.sub_bg
        self._status_badge.border = ft.Border.all(1, tokens.card_border)
        self._console_card_frame.bgcolor = tokens.card_bg
        self._console_card_frame.border = ft.Border.all(1, tokens.card_border)
        safe_update(self)
