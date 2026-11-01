"""Componente del Viewport de Diagnósticos 'Rayos X' y métricas en Flet."""

from typing import Any
import flet as ft
from autorod.infrastructure.ui.flet.theme import ThemeManager, ThemeTokens
from autorod.infrastructure.ui.flet.components.metric_card import FletMetricCard
from autorod.infrastructure.ui.flet.utils import safe_update


class FletDiagnosticsViewport(ft.Container):
    """Viewport de visualización en tiempo real a 60 FPS con tarjetas métricas."""

    def __init__(
        self,
        theme_manager: ThemeManager | None = None
    ) -> None:
        self._theme_mgr = theme_manager or ThemeManager.get_instance()
        self._theme: ThemeTokens = self._theme_mgr.current

        self.image_control = ft.Image(
            src=b"",
            fit=ft.BoxFit.CONTAIN,
            border_radius=10,
            expand=True
        )

        self._status_badge = ft.Text("🟢 RASTREANDO OBJETIVOS", size=10, weight=ft.FontWeight.BOLD, color=self._theme.primary)
        self._res_badge = ft.Text("640x480 (Escala 1:1)", size=10, color="#9ca3af")
        self._mode_badge = ft.Text("⚡ Invariante a Escala", size=10, weight=ft.FontWeight.BOLD, color="#38bdf8")

        hud_bar = ft.Container(
            content=ft.Row(
                controls=[
                    self._status_badge,
                    ft.Row(controls=[self._mode_badge, self._res_badge], spacing=12)
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
            ),
            padding=ft.Padding.symmetric(horizontal=12, vertical=6),
            bgcolor="#131520",
            border_radius=8,
            margin=ft.Margin.only(bottom=6)
        )

        viewport_frame = ft.Container(
            content=ft.Column(
                controls=[
                    hud_bar,
                    ft.Container(
                        content=self.image_control,
                        alignment=ft.Alignment(0, 0),
                        expand=True,
                        bgcolor="#07080b",
                        border_radius=10,
                        border=ft.Border.all(1, "#181a24")
                    )
                ],
                expand=True
            ),
            expand=True,
            bgcolor="#10121a",
            border=ft.Border.all(1, "#1e2232"),
            border_radius=12,
            padding=ft.Padding.all(8)
        )

        self.card_motor = FletMetricCard(
            title="ESTADO DEL MOTOR",
            default_val="🔍 RASTREANDO...",
            subtext="Escaneo continuo",
            theme_manager=self._theme_mgr
        )
        self.card_cache = FletMetricCard(
            title="CACHÉ DE TAMAÑO",
            default_val="Buscando...",
            subtext="Ahorro CPU activo",
            theme_manager=self._theme_mgr
        )
        self.card_monitor = FletMetricCard(
            title="MONITOR CAPTURA",
            default_val="Monitor 1",
            subtext="MSS Ingesta Física",
            theme_manager=self._theme_mgr
        )
        self.card_latencia = FletMetricCard(
            title="LATENCIA ESTIMADA",
            default_val="< 20 ms",
            subtext="Objetivo: 60 FPS",
            theme_manager=self._theme_mgr
        )

        cards_row = ft.Row(
            controls=[
                self.card_motor,
                self.card_cache,
                self.card_monitor,
                self.card_latencia
            ],
            spacing=8
        )

        super().__init__(
            content=ft.Column(
                controls=[
                    viewport_frame,
                    cards_row
                ],
                spacing=8,
                expand=True
            ),
            expand=True,
            padding=ft.Padding.all(12)
        )

        self._theme_mgr.subscribe(self._on_theme_updated)

    def _on_theme_updated(self, tokens: ThemeTokens) -> None:
        self._theme = tokens
        self._status_badge.color = tokens.primary
        safe_update(self)

    def update_image(self, img_bytes: bytes) -> None:
        self.image_control.src = img_bytes
        safe_update(self.image_control)
