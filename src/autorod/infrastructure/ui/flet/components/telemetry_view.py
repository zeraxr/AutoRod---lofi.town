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
            size=26,
            weight=ft.FontWeight.W_700,
            color=self._tokens.text_primary
        )
        self._subtitle_text = ft.Text(
            "Métricas de rendimiento del pipeline y registro de eventos en vivo.",
            size=12,
            color=self._tokens.text_secondary
        )

        self._clear_btn = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.CLEAR_ALL_ROUNDED, size=14, color=self._tokens.text_primary),
                    ft.Text("Limpiar consola", size=12, color=self._tokens.text_primary, weight=ft.FontWeight.W_500)
                ],
                spacing=6,
                alignment=ft.MainAxisAlignment.CENTER
            ),
            bgcolor=self._tokens.sub_bg,
            border=ft.Border.all(1, self._tokens.card_border),
            border_radius=8,
            height=34,
            padding=ft.Padding.symmetric(horizontal=12),
            on_click=self.clear_logs,
            tooltip="Limpiar todos los registros en pantalla",
            ink=True
        )

        self._status_badge = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Container(width=7, height=7, border_radius=4, bgcolor="#10b981"),
                    ft.Text("PIPELINE ACTIVO · 60 FPS", size=11, weight=ft.FontWeight.BOLD, color="#10b981")
                ],
                spacing=6,
                vertical_alignment=ft.CrossAxisAlignment.CENTER
            ),
            bgcolor=self._tokens.sub_bg,
            border=ft.Border.all(1, self._tokens.card_border),
            border_radius=8,
            height=34,
            padding=ft.Padding.symmetric(horizontal=12)
        )

        header = ft.Row(
            controls=[
                ft.Column(
                    controls=[self._title_text, self._subtitle_text],
                    spacing=2
                ),
                ft.Row(
                    controls=[
                        self._status_badge,
                        self._clear_btn
                    ],
                    spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER
                )
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER
        )

        # ---------------------------------------------------------------------
        # 1. TARJETAS DE MÉTRICAS (Figma 72:4730)
        # ---------------------------------------------------------------------
        def _create_metric_card(title: str, val_text: str, subtitle: str) -> tuple[ft.Container, ft.Text]:
            val_ctrl = ft.Text(val_text, size=18, weight=ft.FontWeight.BOLD, color=self._tokens.primary)
            card = ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text(title, size=11, weight=ft.FontWeight.W_600, color=self._tokens.text_secondary),
                        val_ctrl,
                        ft.Text(subtitle, size=10.5, color=self._tokens.text_muted)
                    ],
                    spacing=3
                ),
                bgcolor=self._tokens.card_bg,
                border=ft.Border.all(1, self._tokens.card_border),
                border_radius=10,
                padding=12,
                expand=True
            )
            return card, val_ctrl

        card_session, self._val_session = _create_metric_card("TIEMPO SESIÓN", "00:00:00", "Tiempo transcurrido")
        card_latency, self._val_latency = _create_metric_card("LATENCIA MEDIA", "16.4 ms", "Captura MSS + Visión")
        card_success, self._val_success = _create_metric_card("CAPTURAS", "0", "Aciertos confirmados")
        card_alerts, self._val_alerts = _create_metric_card("ALERTAS", "0", "Recuperaciones de objetivo")

        metrics_row = ft.Row(
            controls=[card_session, card_latency, card_success, card_alerts],
            spacing=12
        )

        # ---------------------------------------------------------------------
        # 2. CONTENEDOR DE CONSOLA ESTILO FIGMA (#0d0f17 con borde #1b2233)
        # ---------------------------------------------------------------------
        self._log_counter_text = ft.Text("Buffer circular · 300 eventos máx.", size=11, color=self._tokens.text_muted)

        console_header_row = ft.Row(
            controls=[
                ft.Text("Consola de Eventos y Diagnósticos", size=13.5, weight=ft.FontWeight.BOLD, color=self._tokens.text_primary),
                self._log_counter_text
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER
        )

        self._inner_console_box = ft.Container(
            content=self._log_column,
            bgcolor="#090b10" if self._tokens.mode == "dark" else "#f8fafc",
            border=ft.Border.all(1, self._tokens.card_border),
            border_radius=8,
            padding=ft.Padding.all(12),
            expand=True
        )

        self._console_card_frame = ft.Container(
            content=ft.Column(
                controls=[
                    console_header_row,
                    self._inner_console_box
                ],
                spacing=10,
                expand=True
            ),
            bgcolor=self._tokens.card_bg,
            border=ft.Border.all(1, self._tokens.card_border),
            border_radius=12,
            padding=ft.Padding.all(16),
            expand=True
        )

        super().__init__(
            content=ft.Column(
                controls=[
                    header,
                    metrics_row,
                    self._console_card_frame
                ],
                spacing=14,
                expand=True
            ),
            expand=True,
            bgcolor=self._tokens.canvas_bg,
            padding=ft.Padding.all(20),
            border_radius=ft.BorderRadius.only(top_left=16, bottom_left=16)
        )

        self.append_log("AutoRod inicializado con arquitectura Clean Architecture SOTA.")
        self.append_log("Pipeline Productor-Consumidor activo a 60 FPS.")

    def clear_logs(self, e: Any = None) -> None:
        """Limpia todos los registros visuales acumulados en la consola."""
        self._log_column.controls.clear()
        self.append_log("Consola reiniciada por el usuario.")
        safe_update(self)

    def append_log(self, message: str) -> None:
        timestamp = time.strftime("%H:%M:%S")
        is_highlight = "iniciado" in message.lower() or "activo" in message.lower() or "guardado" in message.lower()
        color = self._tokens.primary if is_highlight else (self._tokens.text_primary if self._tokens.mode == "light" else "#e4e4e7")
        line = ft.Text(
            f"[{timestamp}] {message}",
            size=11,
            color=color,
            font_family="Consolas"
        )
        self._log_column.controls.append(line)
        if len(self._log_column.controls) > 300:
            self._log_column.controls.pop(0)

        safe_update(self)

    def update_metrics(self, session_str: str, latency_ms: float, catches: int, alerts: int) -> None:
        self._val_session.value = session_str
        self._val_latency.value = f"{latency_ms:.1f} ms"
        self._val_success.value = str(catches)
        self._val_alerts.value = str(alerts)
        safe_update(self)

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
        self._inner_console_box.bgcolor = "#090b10" if tokens.mode == "dark" else "#f8fafc"
        self._inner_console_box.border = ft.Border.all(1, tokens.card_border)
        safe_update(self)
