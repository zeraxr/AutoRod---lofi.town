"""Componente del Viewport de Diagnósticos y panel de Parámetros en Flet."""

from typing import Callable, Any
from pathlib import Path
import flet as ft
from autorod.infrastructure.ui.flet.theme import ThemeManager, ThemeTokens
from autorod.infrastructure.ui.flet.components.metric_card import FletMetricCard
from autorod.infrastructure.ui.flet.utils import safe_update, get_asset_path


class FletDiagnosticsViewport(ft.Container):
    """
    Vista unificada del Dashboard al estilo Antigravity / Eclipse:
    - Área de Visualización (Izquierda): Visor en vivo a 60 FPS o Standby con logo e indicaciones.
    - Panel de Parámetros (Derecha): Métricas de estado, monitor, latencia y botón para vaciar caché con flechas en bucle.
    """

    def __init__(
        self,
        theme_manager: ThemeManager | None = None,
        on_clear_cache: Callable[[], None] | None = None
    ) -> None:
        self._theme_mgr = theme_manager or ThemeManager.get_instance()
        self._theme: ThemeTokens = self._theme_mgr.current
        self._on_clear_cache = on_clear_cache
        self._is_preview_active = False
        self._is_bot_running = False

        # 1. Contenedor de Fotogramas de Diagnóstico
        self.image_control = ft.Image(
            src=b"",
            fit=ft.BoxFit.CONTAIN,
            border_radius=8,
            expand=True
        )
        self._image_container = ft.Container(
            content=self.image_control,
            alignment=ft.Alignment(0, 0),
            expand=True,
            bgcolor="#08080a",
            border_radius=8,
            border=ft.Border.all(1, "#181922")
        )

        # 2. Vista de Standby con el Logo Oficial del Software e Indicaciones
        logo_path = get_asset_path("icons/logo.png")
        if not logo_path.is_file():
            logo_path = get_asset_path("icons/logo_48.png")

        logo_image = ft.Image(
            src=str(logo_path),
            width=64,
            height=64,
            fit=ft.BoxFit.CONTAIN
        )

        self._standby_dot = ft.Container(width=6, height=6, border_radius=3, bgcolor="#f59e0b")
        self._standby_label = ft.Text("BOT EN PAUSA", size=10, weight=ft.FontWeight.BOLD, color="#f59e0b")
        self._standby_status_badge = ft.Container(
            content=ft.Row(
                controls=[self._standby_dot, self._standby_label],
                spacing=6,
                alignment=ft.MainAxisAlignment.CENTER
            ),
            bgcolor="#1f180d",
            border=ft.Border.all(1, "#3d2c14"),
            border_radius=6,
            padding=ft.Padding.symmetric(horizontal=10, vertical=4)
        )

        def _instruction_chip(key_text: str, desc: str, icon_name: Any) -> ft.Container:
            return ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Icon(icon_name, size=14, color="#94a3b8"),
                        ft.Container(
                            content=ft.Text(key_text, size=10, weight=ft.FontWeight.BOLD, color="#f4f4f5", font_family="Consolas"),
                            bgcolor="#1c1d27",
                            border_radius=4,
                            padding=ft.Padding.symmetric(horizontal=6, vertical=2)
                        ),
                        ft.Text(desc, size=11, color="#9ca3af")
                    ],
                    spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER
                ),
                bgcolor="#12131b",
                border=ft.Border.all(1, "#1b1c26"),
                border_radius=8,
                padding=ft.Padding.symmetric(horizontal=12, vertical=7),
                width=270
            )

        instructions_column = ft.Column(
            controls=[
                _instruction_chip("SHIFT + Q", "Iniciar o pausar bot", ft.Icons.PLAY_CIRCLE_OUTLINE_ROUNDED),
                _instruction_chip("VISUALIZAR", "Previsualizar área de trabajo", ft.Icons.VISIBILITY_ROUNDED),
                _instruction_chip("Q", "Parada de emergencia", ft.Icons.POWER_SETTINGS_NEW_ROUNDED),
            ],
            spacing=6,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )

        self._standby_view = ft.Container(
            content=ft.Column(
                controls=[
                    logo_image,
                    ft.Text("AutoRod", size=18, weight=ft.FontWeight.BOLD, color="#f8fafc"),
                    self._standby_status_badge,
                    ft.Container(height=6),
                    instructions_column,
                    ft.Container(height=4),
                    ft.Text(
                        "Haz clic en 'Visualizar' en la barra superior para ver el área de trabajo en tiempo real.",
                        size=11,
                        color="#71717a",
                        text_align=ft.TextAlign.CENTER
                    )
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=6
            ),
            alignment=ft.Alignment(0, 0),
            expand=True,
            bgcolor="#08080a",
            border_radius=8,
            border=ft.Border.all(1, "#181922")
        )

        self._center_switcher = ft.AnimatedSwitcher(
            content=self._standby_view,
            transition=ft.AnimatedSwitcherTransition.FADE,
            duration=180,
            reverse_duration=120,
            expand=True
        )

        # 3. HUD Superior del Visor
        self._status_dot = ft.Container(
            width=6,
            height=6,
            border_radius=3,
            bgcolor="#f59e0b"
        )
        self._status_text = ft.Text("EN ESPERA (PAUSADO)", size=10, weight=ft.FontWeight.BOLD, color="#f59e0b")
        self._status_badge = ft.Row(controls=[self._status_dot, self._status_text], spacing=6)

        self._res_badge = ft.Text("640x480", size=10, color="#71717a")
        self._mode_badge = ft.Text("Standby", size=10, weight=ft.FontWeight.BOLD, color="#9ca3af")

        hud_bar = ft.Container(
            content=ft.Row(
                controls=[
                    self._status_badge,
                    ft.Row(controls=[self._mode_badge, self._res_badge], spacing=12)
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
            ),
            padding=ft.Padding.symmetric(horizontal=12, vertical=6),
            bgcolor="#14151c",
            border=ft.Border.all(1, "#1e1f29"),
            border_radius=6,
            margin=ft.Margin.only(bottom=6)
        )

        viewport_frame = ft.Container(
            content=ft.Column(
                controls=[
                    hud_bar,
                    self._center_switcher
                ],
                expand=True
            ),
            expand=True,
            bgcolor="#111218",
            border=ft.Border.all(1, "#1a1b24"),
            border_radius=10,
            padding=ft.Padding.all(8)
        )

        # 4. Botón de Vaciar Caché con Icono de Flechas en Loop
        self._clear_cache_btn = ft.IconButton(
            icon=ft.Icons.AUTORENEW_ROUNDED,
            icon_size=16,
            icon_color="#94a3b8",
            tooltip="Borrar memoria caché de dimensiones (Recalibrar)",
            on_click=self._handle_clear_cache,
            style=ft.ButtonStyle(
                bgcolor={ft.ControlState.HOVERED: "#20212d", ft.ControlState.DEFAULT: "#181924"},
                shape=ft.RoundedRectangleBorder(radius=6),
                padding=ft.Padding.all(4)
            )
        )

        # 5. Tarjetas de Parámetros del Sistema (Panel Lateral Derecho)
        self.card_motor = FletMetricCard(
            title="ESTADO DEL MOTOR",
            default_val="PAUSADO [Shift+Q]",
            subtext="En espera para iniciar",
            theme_manager=self._theme_mgr
        )
        self.card_cache = FletMetricCard(
            title="CACHÉ DE TAMAÑO",
            default_val="Buscando...",
            subtext="Ahorro CPU activo",
            theme_manager=self._theme_mgr,
            action_control=self._clear_cache_btn
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

        params_header = ft.Row(
            controls=[
                ft.Icon(ft.Icons.TUNE_ROUNDED, size=15, color="#a1a1aa"),
                ft.Text("Parámetros", size=13, weight=ft.FontWeight.BOLD, color="#f4f4f5")
            ],
            spacing=6,
            vertical_alignment=ft.CrossAxisAlignment.CENTER
        )

        parameters_panel = ft.Container(
            content=ft.Column(
                controls=[
                    params_header,
                    self.card_motor,
                    self.card_cache,
                    self.card_monitor,
                    self.card_latencia
                ],
                spacing=8,
                expand=True
            ),
            width=265,
            bgcolor="#111218",
            border=ft.Border.all(1, "#1a1b24"),
            border_radius=10,
            padding=ft.Padding.all(12)
        )

        # Layout unificado: Visor principal a la izquierda, Parámetros a la derecha
        dashboard_layout = ft.Row(
            controls=[
                viewport_frame,
                parameters_panel
            ],
            spacing=10,
            expand=True
        )

        super().__init__(
            content=dashboard_layout,
            expand=True,
            bgcolor="#0f1015",
            padding=ft.Padding.all(10)
        )

        self._theme_mgr.subscribe(self._on_theme_updated)

    def _handle_clear_cache(self, e: Any = None) -> None:
        """Dispara el callback para purgar la caché y muestra confirmación visual."""
        self.card_cache.update_val("Recalibrando...", color="#38bdf8", sub="Caché purgado")
        if self._on_clear_cache:
            try:
                self._on_clear_cache()
            except Exception:
                pass
        safe_update(self.card_cache)

    def _on_theme_updated(self, tokens: ThemeTokens) -> None:
        self._theme = tokens
        if self._is_preview_active:
            self._status_dot.bgcolor = tokens.primary
            self._status_text.color = tokens.primary
        if self._is_bot_running:
            self._standby_dot.bgcolor = tokens.primary
            self._standby_label.color = tokens.primary
            self._standby_status_badge.bgcolor = tokens.accent_subtle
            self._standby_status_badge.border = ft.Border.all(1, tokens.border_active)
        safe_update(self)

    def set_preview_active(self, active: bool) -> None:
        """Alterna entre la previsualización del juego y la pantalla de Standby informativa."""
        self._is_preview_active = active
        if active:
            self._center_switcher.content = self._image_container
            self._status_dot.bgcolor = self._theme.primary
            self._status_text.value = "VISOR ACTIVO"
            self._status_text.color = self._theme.primary
            self._mode_badge.value = "Captura MSS en Vivo"
            self._mode_badge.color = "#38bdf8"
        else:
            self._center_switcher.content = self._standby_view
            self._status_dot.bgcolor = "#f59e0b"
            self._status_text.value = "EN ESPERA (PAUSADO)" if not self._is_bot_running else "BOT ACTIVO"
            self._status_text.color = "#f59e0b" if not self._is_bot_running else self._theme.primary
            self._mode_badge.value = "Standby"
            self._mode_badge.color = "#9ca3af"
        safe_update(self)

    def set_bot_running(self, running: bool) -> None:
        """Actualiza las insignias de estado según si el bot está ejecutándose o pausado."""
        self._is_bot_running = running
        if running:
            self._standby_dot.bgcolor = self._theme.primary
            self._standby_label.value = "BOT ACTIVO"
            self._standby_label.color = self._theme.primary
            self._standby_status_badge.bgcolor = self._theme.accent_subtle
            self._standby_status_badge.border = ft.Border.all(1, self._theme.border_active)
            if not self._is_preview_active:
                self._status_dot.bgcolor = self._theme.primary
                self._status_text.value = "BOT ACTIVO"
                self._status_text.color = self._theme.primary
        else:
            self._standby_dot.bgcolor = "#f59e0b"
            self._standby_label.value = "BOT EN PAUSA"
            self._standby_label.color = "#f59e0b"
            self._standby_status_badge.bgcolor = "#1f180d"
            self._standby_status_badge.border = ft.Border.all(1, "#3d2c14")
            if not self._is_preview_active:
                self._status_dot.bgcolor = "#f59e0b"
                self._status_text.value = "EN ESPERA (PAUSADO)"
                self._status_text.color = "#f59e0b"
        safe_update(self)

    def update_image(self, img_bytes: bytes) -> None:
        self.image_control.src = img_bytes
        if self._is_preview_active:
            safe_update(self.image_control)
