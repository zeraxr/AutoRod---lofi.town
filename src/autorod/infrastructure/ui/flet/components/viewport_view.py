"""Componente del Viewport de Diagnósticos y panel de Métricas en Flet (Diseño Figma Oficial)."""

from typing import Callable, Any
from pathlib import Path
from datetime import datetime
import random
import flet as ft
from autorod.infrastructure.ui.flet.theme import ThemeManager, ThemeTokens
from autorod.infrastructure.ui.flet.components.metric_card import FletMetricCard
from autorod.infrastructure.ui.flet.utils import safe_update, get_asset_path


def get_time_based_greeting(dt: datetime | None = None) -> str:
    """
    Retorna el saludo correspondiente según la hora local del sistema:
    - 06:00 a 11:59: ¡Buenos días!
    - 12:00 a 19:59: ¡Buenas tardes!
    - 20:00 a 05:59: ¡Buenas noches!
    """
    hour = (dt or datetime.now()).hour
    if 6 <= hour < 12:
        return "¡Buenos días!"
    elif 12 <= hour < 20:
        return "¡Buenas tardes!"
    else:
        return "¡Buenas noches!"


MINECRAFT_SPLASH_PHRASES: list[str] = [
    "¡Procura beber agua! :)",
    "¡Eres importante, nunca lo olvides!",
    "¡Otro día de pesca, otro día de farmeo! :3",
    "El omega 3!! El omega 3!!!! D::::",
    "¡No bajes los brazos! Mucho ánimo!!",
    "¡Una buena postura previene dolores de espalda!",
    "¡Los peces legendarios te están esperando!",
    "¡Paciencia y buena caña! :D",
    "¡Asegúrate de parpadear de vez en cuando! o.o",
    "¡Que la suerte del pescador te acompañe hoy!",
    "¡El río fluye, el farmeo no para!",
    "¡Un descanso de 5 minutos hace maravillas!",
    "¡Hora de llenar ese inventario!",
    "¡Respira hondo y disfruta la jornada!",
    "¡Recuerda estirar las piernas un poco!",
    "¡El mar premia a los constantes!",
    "¡Pescador precavido vale por dos!",
]


def get_random_splash_phrase() -> str:
    """Obtiene una frase aleatoria estilo splash text de Minecraft."""
    return random.choice(MINECRAFT_SPLASH_PHRASES)


class FletDiagnosticsViewport(ft.Container):
    """
    Vista unificada del Dashboard diseñada en Figma (Tokyo Night / Navy):
    - Presentación superior: Saludo según hora ("¡Buenos días!", "¡Buenas tardes!", "¡Buenas noches!")
      y frases aleatorias estilo Minecraft ("¡Procura beber agua! :)", etc.).
    - Botones rápidos ("pausar", "iniciar").
    - Contenedor "Previsualización y métricas" (#0d0f17 con borde #1b2233).
    - Tarjetas métricas horizontales (#141a2a) y visor en vivo de captura a 60 FPS.
    """

    def __init__(
        self,
        theme_manager: ThemeManager | None = None,
        on_clear_cache: Callable[[], None] | None = None,
        on_toggle_bot: Callable[[], None] | None = None,
        config: Any | None = None
    ) -> None:
        self._theme_mgr = theme_manager or ThemeManager.get_instance()
        self._theme: ThemeTokens = self._theme_mgr.current
        self._on_clear_cache = on_clear_cache
        self._on_toggle_bot = on_toggle_bot
        self._config = config
        self._is_preview_active = False
        self._is_bot_running = False
        self._show_greetings: bool = getattr(config, "show_greetings", True) if config else True
        self._use_local_time: bool = getattr(config, "use_local_time", True) if config else True
        self._custom_accent: str = self._theme.primary

        # ---------------------------------------------------------------------
        # 1. PRESENTACIÓN: SALUDO DINÁMICO Y BOTONES DE ACCIÓN RÁPIDA (Figma 43:6)
        # ---------------------------------------------------------------------
        initial_greeting = get_time_based_greeting() if self._use_local_time else "¡Bienvenido a AutoRod!"
        self._greeting_text = ft.Text(
            initial_greeting,
            size=26,
            weight=ft.FontWeight.W_700,
            color="#ffffff"
        )

        self._splash_text = ft.Text(
            get_random_splash_phrase(),
            size=12,
            color="#a5b4ff"
        )

        self._splash_container = ft.Container(
            content=self._splash_text,
            on_click=lambda _: self.cycle_splash_phrase(),
            tooltip="Haz clic para otra frase :D",
            border_radius=4,
            padding=ft.Padding.symmetric(horizontal=2, vertical=1)
        )

        self._greeting_col = ft.Column(
            controls=[
                self._greeting_text,
                self._splash_container
            ],
            spacing=2,
            visible=self._show_greetings
        )

        self._quick_pause_btn = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.PAUSE_ROUNDED, size=14, color="#ffffff"),
                    ft.Text("pausar", size=12, color="#ffffff", weight=ft.FontWeight.W_500)
                ],
                spacing=6,
                alignment=ft.MainAxisAlignment.CENTER
            ),
            bgcolor="#141a2a",
            border=ft.Border.all(1, self._custom_accent),
            border_radius=8,
            height=34,
            padding=ft.Padding.symmetric(horizontal=13),
            on_click=self._on_pause_click,
            tooltip="Pausar ejecución del bot [Shift + Q]",
            ink=True
        )

        self._quick_play_btn = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.PLAY_ARROW_ROUNDED, size=14, color="#ffffff"),
                    ft.Text("iniciar", size=12, color="#ffffff", weight=ft.FontWeight.W_500)
                ],
                spacing=6,
                alignment=ft.MainAxisAlignment.CENTER
            ),
            bgcolor=self._custom_accent,
            border=ft.Border.all(1, self._custom_accent),
            border_radius=8,
            height=34,
            padding=ft.Padding.symmetric(horizontal=13),
            on_click=self._on_play_click,
            tooltip="Iniciar o reanudar bot [Shift + Q]",
            ink=True
        )

        presentation_header = ft.Row(
            controls=[
                self._greeting_col,
                ft.Row(
                    controls=[
                        self._quick_pause_btn,
                        self._quick_play_btn
                    ],
                    spacing=8
                )
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER
        )

        # ---------------------------------------------------------------------
        # 2. CONTENEDOR DE FOTOGRAMAS (EN VIVO)
        # ---------------------------------------------------------------------
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

        # ---------------------------------------------------------------------
        # 3. TARJETAS MÉTRICAS (Figma 43:57)
        # ---------------------------------------------------------------------
        self._clear_cache_btn = ft.IconButton(
            icon=ft.Icons.AUTORENEW_ROUNDED,
            icon_size=15,
            icon_color="#a5b4ff",
            tooltip="Borrar memoria caché de dimensiones (Recalibrar)",
            on_click=self._handle_clear_cache,
            style=ft.ButtonStyle(
                bgcolor={ft.ControlState.HOVERED: "#1e263d", ft.ControlState.DEFAULT: "#182033"},
                shape=ft.RoundedRectangleBorder(radius=6),
                padding=ft.Padding.all(4)
            )
        )

        self.card_motor = FletMetricCard(
            title="ESTADO",
            default_val="PAUSADO [Shift+Q]",
            subtext="En espera para iniciar",
            theme_manager=self._theme_mgr
        )
        self.card_cache = FletMetricCard(
            title="TAMAÑO DE CACHÉ",
            default_val="Esperando objetivo",
            subtext="Ahorro CPU activo",
            theme_manager=self._theme_mgr,
            action_control=self._clear_cache_btn
        )
        self.card_monitor = FletMetricCard(
            title="MONITOR",
            default_val="Monitor 1",
            subtext="MSS Ingesta Física",
            theme_manager=self._theme_mgr
        )
        self.card_latencia = FletMetricCard(
            title="LATENCIA ESTIMADA",
            default_val="< 20 ms, objetivo: 60 FPS",
            subtext="Objetivo: 60 FPS",
            theme_manager=self._theme_mgr
        )

        # Insignias de compatibilidad
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

        cards_stack = ft.Column(
            controls=[
                self.card_motor,
                self.card_cache,
                self.card_monitor,
                self.card_latencia
            ],
            spacing=8,
            expand=True
        )

        self._standby_view = ft.Container(
            content=cards_stack,
            expand=True
        )

        self._center_switcher = ft.AnimatedSwitcher(
            content=self._standby_view,
            transition=ft.AnimatedSwitcherTransition.FADE,
            duration=180,
            reverse_duration=120,
            expand=True
        )

        # ---------------------------------------------------------------------
        # 4. CABECERA DE PREVISUALIZACIÓN Y MÉTRICAS (Figma 43:21)
        # ---------------------------------------------------------------------
        self._status_dot = ft.Container(width=6, height=6, border_radius=3, bgcolor="#f59e0b")
        self._status_text = ft.Text("EN ESPERA (PAUSADO)", size=10, weight=ft.FontWeight.BOLD, color="#f59e0b")
        self._status_badge = ft.Row(controls=[self._status_dot, self._status_text], spacing=6)

        self._res_badge = ft.Text("1920×1080 · vista adaptada al panel", size=11, color="#a5b4ff")
        self._mode_badge = ft.Text("Standby", size=10, weight=ft.FontWeight.BOLD, color="#9ca3af")

        self._preview_title_text = ft.Text("Previsualización de pantalla", size=13.5, weight=ft.FontWeight.BOLD, color=self._theme.text_primary)
        preview_header_row = ft.Row(
            controls=[
                ft.Column(
                    controls=[
                        self._preview_title_text,
                        self._res_badge
                    ],
                    spacing=2
                ),
                ft.Row(
                    controls=[
                        self._status_badge,
                        ft.Container(width=4),
                        self._mode_badge
                    ],
                    spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER
                )
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER
        )

        self._preview_card_frame = ft.Container(
            content=ft.Column(
                controls=[
                    preview_header_row,
                    ft.Container(height=6),
                    self._center_switcher
                ],
                expand=True,
                spacing=8
            ),
            bgcolor=self._theme.card_bg,
            border=ft.Border.all(1, self._theme.card_border),
            border_radius=12,
            padding=ft.Padding.all(16),
            expand=True
        )

        super().__init__(
            content=ft.Column(
                controls=[
                    presentation_header,
                    ft.Container(height=4),
                    self._preview_card_frame
                ],
                spacing=12,
                expand=True
            ),
            expand=True,
            bgcolor=self._theme.canvas_bg,
            padding=ft.Padding.all(20),
            border_radius=ft.BorderRadius.only(top_left=16, bottom_left=16)
        )

        self._theme_mgr.subscribe(self._on_theme_updated)

    def _on_pause_click(self, e: Any = None) -> None:
        if self._is_bot_running and self._on_toggle_bot:
            self._on_toggle_bot()

    def _on_play_click(self, e: Any = None) -> None:
        if not self._is_bot_running and self._on_toggle_bot:
            self._on_toggle_bot()

    def _handle_clear_cache(self, e: Any = None) -> None:
        """Dispara el callback para purgar la caché y muestra confirmación visual."""
        self.card_cache.update_val("Recalibrando...", color="#38bdf8", sub="Caché purgado")
        if self._on_clear_cache:
            try:
                self._on_clear_cache()
            except Exception:
                pass
        safe_update(self.card_cache)

    def apply_button_theme(self, color: str) -> None:
        """
        Aplica el color de acento personalizado:
        - Cambia el color del contorno de pausar.
        - Cambia el relleno de Iniciar.
        Sólamente eso.
        """
        self._custom_accent = color
        self._quick_pause_btn.border = ft.Border.all(1, color)
        if not self._is_bot_running:
            self._quick_play_btn.bgcolor = color
            self._quick_play_btn.border = ft.Border.all(1, color)
        safe_update(self._quick_pause_btn)
        safe_update(self._quick_play_btn)

    def set_show_greetings(self, show: bool) -> None:
        """Muestra u oculta la sección de saludos y frases dinámicas."""
        self._show_greetings = show
        self._greeting_col.visible = show
        safe_update(self._greeting_col)

    def set_use_local_time(self, use_local: bool) -> None:
        """Activa el saludo según hora local o muestra un saludo neutro fijo."""
        self._use_local_time = use_local
        if use_local:
            self._greeting_text.value = get_time_based_greeting()
        else:
            self._greeting_text.value = "¡Bienvenido a AutoRod!"
        safe_update(self._greeting_text)

    def _on_theme_updated(self, tokens: ThemeTokens) -> None:
        self._theme = tokens
        self.bgcolor = tokens.canvas_bg
        self._preview_card_frame.bgcolor = tokens.card_bg
        self._preview_card_frame.border = ft.Border.all(1, tokens.card_border)
        self._greeting_text.color = tokens.text_primary
        self._splash_text.color = tokens.text_secondary
        self._preview_title_text.color = tokens.text_primary
        self._res_badge.color = tokens.text_secondary
        self._quick_pause_btn.bgcolor = tokens.sub_bg
        self.apply_button_theme(tokens.primary)
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
            self._status_dot.bgcolor = self._custom_accent
            self._status_text.value = "VISOR ACTIVO"
            self._status_text.color = self._custom_accent
            self._mode_badge.value = "Captura MSS en Vivo"
            self._mode_badge.color = "#38bdf8"
        else:
            self._center_switcher.content = self._standby_view
            self._status_dot.bgcolor = "#f59e0b"
            self._status_text.value = "EN ESPERA (PAUSADO)" if not self._is_bot_running else "BOT ACTIVO"
            self._status_text.color = "#f59e0b" if not self._is_bot_running else self._custom_accent
            self._mode_badge.value = "Standby"
            self._mode_badge.color = "#9ca3af"
        safe_update(self)

    def set_bot_running(self, running: bool) -> None:
        """Actualiza las insignias de estado según si el bot está ejecutándose o pausado."""
        self._is_bot_running = running
        accent = getattr(self, "_custom_accent", self._theme.primary)
        if running:
            self._standby_dot.bgcolor = accent
            self._standby_label.value = "BOT ACTIVO"
            self._standby_label.color = accent
            self._standby_status_badge.bgcolor = self._theme.accent_subtle
            self._standby_status_badge.border = ft.Border.all(1, self._theme.border_active)
            self._quick_play_btn.bgcolor = "#3d3cac"
            self._quick_pause_btn.bgcolor = "#1e263d"
            self._quick_pause_btn.border = ft.Border.all(1, accent)
            if not self._is_preview_active:
                self._status_dot.bgcolor = accent
                self._status_text.value = "BOT ACTIVO"
                self._status_text.color = accent
        else:
            self._standby_dot.bgcolor = "#f59e0b"
            self._standby_label.value = "BOT EN PAUSA"
            self._standby_label.color = "#f59e0b"
            self._standby_status_badge.bgcolor = "#1f180d"
            self._standby_status_badge.border = ft.Border.all(1, "#3d2c14")
            self._quick_play_btn.bgcolor = accent
            self._quick_play_btn.border = ft.Border.all(1, accent)
            self._quick_pause_btn.bgcolor = "#141a2a"
            self._quick_pause_btn.border = ft.Border.all(1, accent)
            if not self._is_preview_active:
                self._status_dot.bgcolor = "#f59e0b"
                self._status_text.value = "EN ESPERA (PAUSADO)"
                self._status_text.color = "#f59e0b"
        safe_update(self)

    def update_image(self, img_bytes: bytes) -> None:
        self.image_control.src = img_bytes
        if self._is_preview_active:
            safe_update(self.image_control)

    def cycle_splash_phrase(self) -> None:
        """Cambia la frase de bienvenida a una nueva de forma aleatoria."""
        current = self._splash_text.value
        candidates = [p for p in MINECRAFT_SPLASH_PHRASES if p != current]
        self._splash_text.value = random.choice(candidates) if candidates else current
        safe_update(self._splash_text)

    def refresh_greeting(self) -> None:
        """Actualiza el saludo si cambia la hora del día y está habilitada la hora local."""
        if not getattr(self, "_use_local_time", True):
            return
        new_greeting = get_time_based_greeting()
        if self._greeting_text.value != new_greeting:
            self._greeting_text.value = new_greeting
            safe_update(self._greeting_text)
