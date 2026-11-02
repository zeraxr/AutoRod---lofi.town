"""Vista de Parámetros de Detección y Ritmo en Flet (Diseño Oficial Figma 1:1)."""

from typing import Callable, Any
import flet as ft
from autorod.infrastructure.ui.flet.theme import ThemeManager, ThemeTokens
from autorod.config import AppConfig, save_config
from autorod.infrastructure.ui.flet.utils import safe_update


class FletParametersView(ft.Container):
    """
    Panel de calibración de detección, confianza, tolerancia cromática y tiempos de ritmo.
    Estrictamente alineado 1:1 con Figma (Frames 72:4888 Modo Oscuro y 78:631 Modo Claro).
    """

    def __init__(
        self,
        config: AppConfig,
        config_path: str = "config.toml",
        on_save_callback: Callable[[AppConfig], None] | None = None,
        theme_manager: ThemeManager | None = None
    ) -> None:
        self._config = config
        self._config_path = config_path
        self._on_save_cb = on_save_callback
        self._theme_mgr = theme_manager or ThemeManager.get_instance()
        self._tokens: ThemeTokens = self._theme_mgr.current

        # ---------------------------------------------------------------------
        # 0. HEADER PRINCIPAL (Figma 72:4888)
        # ---------------------------------------------------------------------
        self._title_text = ft.Text(
            "Parámetros",
            size=26,
            weight=ft.FontWeight.W_700,
            color=self._tokens.text_primary
        )
        self._subtitle_text = ft.Text(
            "Calibración del algoritmo de detección y tiempos de pesca.",
            size=12,
            color=self._tokens.text_secondary
        )

        self._badge_profile_text = ft.Text(
            f"PERFIL: {self._config.profile.upper()}",
            size=10,
            weight=ft.FontWeight.W_700,
            color=self._tokens.primary
        )
        self._profile_badge = ft.Container(
            content=self._badge_profile_text,
            bgcolor=self._tokens.sub_bg,
            border=ft.Border.all(1, self._tokens.card_border),
            border_radius=6,
            padding=ft.Padding.symmetric(horizontal=10, vertical=6)
        )

        header = ft.Row(
            controls=[
                ft.Column(
                    controls=[self._title_text, self._subtitle_text],
                    spacing=2
                ),
                self._profile_badge
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER
        )

        # ---------------------------------------------------------------------
        # 1. TARJETA: PERFIL ACTIVO
        # ---------------------------------------------------------------------
        self._profile_dropdown = ft.Dropdown(
            options=[
                ft.DropdownOption("balanced", "Pesca equilibrada (Recomendado para empezar)"),
                ft.DropdownOption("fast", "Pesca rápida (Menor latencia y respuestas ágiles)"),
                ft.DropdownOption("high_precision", "Alta precisión (Ideal para entornos con variación de luz)")
            ],
            value=self._config.profile,
            bgcolor=self._tokens.card_bg,
            border_color=self._tokens.card_border,
            focused_border_color=self._tokens.primary,
            text_size=12,
            content_padding=ft.Padding.symmetric(horizontal=12, vertical=8),
            on_select=self._on_profile_changed
        )

        profile_card = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.AUTO_AWESOME_ROUNDED, size=16, color=self._tokens.primary),
                            ft.Text("Perfil Activo", size=14, weight=ft.FontWeight.W_600, color=self._tokens.text_primary)
                        ],
                        spacing=8
                    ),
                    ft.Text(
                        "Selecciona un perfil optimizado o ajusta las variables para crear una configuración a tu medida.",
                        size=11.5,
                        color=self._tokens.text_secondary
                    ),
                    self._profile_dropdown
                ],
                spacing=10
            ),
            bgcolor=self._tokens.card_bg,
            border=ft.Border.all(1, self._tokens.card_border),
            border_radius=12,
            padding=16
        )

        # ---------------------------------------------------------------------
        # 2. TARJETA: DETECCIÓN DE OBJETIVO (VISIÓN)
        # ---------------------------------------------------------------------
        self._conf_badge = ft.Text(
            f"{int(self._config.min_confidence * 100)}%",
            size=12,
            weight=ft.FontWeight.BOLD,
            color=self._tokens.primary
        )
        self._conf_slider = ft.Slider(
            min=50,
            max=99,
            divisions=49,
            value=int(self._config.min_confidence * 100),
            active_color=self._tokens.primary,
            inactive_color=self._tokens.card_border,
            on_change=self._on_conf_change
        )

        self._color_tol_badge = ft.Text(
            f"{int(self._config.color_tolerance * 100)}%",
            size=12,
            weight=ft.FontWeight.BOLD,
            color=self._tokens.primary
        )
        self._color_tol_slider = ft.Slider(
            min=5,
            max=50,
            divisions=45,
            value=int(self._config.color_tolerance * 100),
            active_color=self._tokens.primary,
            inactive_color=self._tokens.card_border,
            on_change=self._on_color_tol_change
        )

        self._search_area_dropdown = ft.Dropdown(
            options=[
                ft.DropdownOption("fullscreen", "Pantalla completa (Escaneo 100% de la ventana)"),
                ft.DropdownOption("center_50", "Zona central 50% (Ahorro notable de CPU/GPU)"),
                ft.DropdownOption("active_area", "Área de juego activa calibrada")
            ],
            value=self._config.search_area,
            bgcolor=self._tokens.card_bg,
            border_color=self._tokens.card_border,
            focused_border_color=self._tokens.primary,
            text_size=12,
            content_padding=ft.Padding.symmetric(horizontal=12, vertical=8)
        )

        detection_card = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.VISIBILITY_ROUNDED, size=16, color=self._tokens.primary),
                            ft.Text("Detección de Objetivo (Visión)", size=14, weight=ft.FontWeight.W_600, color=self._tokens.text_primary)
                        ],
                        spacing=8
                    ),
                    # Slider Confianza
                    ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Text("Confianza mínima requerida", size=12, weight=ft.FontWeight.W_500, color=self._tokens.text_primary),
                                    self._conf_badge
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                            ),
                            ft.Text("Umbral de certeza visual para validar el anzuelo y las burbujas.", size=11, color=self._tokens.text_secondary),
                            self._conf_slider
                        ],
                        spacing=2
                    ),
                    # Slider Tolerancia de Color
                    ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Text("Tolerancia de color", size=12, weight=ft.FontWeight.W_500, color=self._tokens.text_primary),
                                    self._color_tol_badge
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                            ),
                            ft.Text("Margen cromático admitido frente a cambios bruscos de iluminación o lluvia.", size=11, color=self._tokens.text_secondary),
                            self._color_tol_slider
                        ],
                        spacing=2
                    ),
                    # Dropdown Área de Búsqueda
                    ft.Column(
                        controls=[
                            ft.Text("Área de escaneo en pantalla", size=12, weight=ft.FontWeight.W_500, color=self._tokens.text_primary),
                            self._search_area_dropdown
                        ],
                        spacing=4
                    )
                ],
                spacing=14
            ),
            bgcolor=self._tokens.card_bg,
            border=ft.Border.all(1, self._tokens.card_border),
            border_radius=12,
            padding=16
        )

        # ---------------------------------------------------------------------
        # 3. TARJETA: RITMO Y SEGURIDAD
        # ---------------------------------------------------------------------
        self._cast_delay_badge = ft.Text(
            f"{self._config.cast_delay_ms} ms",
            size=12,
            weight=ft.FontWeight.BOLD,
            color=self._tokens.primary
        )
        self._cast_delay_slider = ft.Slider(
            min=500,
            max=4000,
            divisions=35,
            value=self._config.cast_delay_ms,
            active_color=self._tokens.primary,
            inactive_color=self._tokens.card_border,
            on_change=self._on_cast_delay_change
        )

        self._max_wait_badge = ft.Text(
            f"{self._config.max_wait_bite_sec} s",
            size=12,
            weight=ft.FontWeight.BOLD,
            color=self._tokens.primary
        )
        self._max_wait_slider = ft.Slider(
            min=10,
            max=60,
            divisions=10,
            value=self._config.max_wait_bite_sec,
            active_color=self._tokens.primary,
            inactive_color=self._tokens.card_border,
            on_change=self._on_max_wait_change
        )

        self._retry_switch = ft.Switch(
            value=self._config.retry_on_lost,
            active_color=self._tokens.primary,
            scale=0.85
        )

        self._consecutive_errors_dropdown = ft.Dropdown(
            options=[
                ft.DropdownOption("2", "2 errores consecutivos"),
                ft.DropdownOption("3", "3 errores consecutivos (Recomendado)"),
                ft.DropdownOption("5", "5 errores consecutivos"),
                ft.DropdownOption("10", "10 errores consecutivos")
            ],
            value=str(self._config.pause_on_consecutive_errors),
            bgcolor=self._tokens.card_bg,
            border_color=self._tokens.card_border,
            focused_border_color=self._tokens.primary,
            text_size=12,
            content_padding=ft.Padding.symmetric(horizontal=12, vertical=8)
        )

        safety_card = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.TIMER_ROUNDED, size=16, color=self._tokens.primary),
                            ft.Text("Ritmo de Lanzamiento y Seguridad", size=14, weight=ft.FontWeight.W_600, color=self._tokens.text_primary)
                        ],
                        spacing=8
                    ),
                    # Espera entre lanzamientos
                    ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Text("Espera entre lanzamientos", size=12, weight=ft.FontWeight.W_500, color=self._tokens.text_primary),
                                    self._cast_delay_badge
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                            ),
                            ft.Text("Pausa tras recoger la captura para volver a arrojar el anzuelo.", size=11, color=self._tokens.text_secondary),
                            self._cast_delay_slider
                        ],
                        spacing=2
                    ),
                    # Tiempo máximo sin picada
                    ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Text("Tiempo máximo sin picada", size=12, weight=ft.FontWeight.W_500, color=self._tokens.text_primary),
                                    self._max_wait_badge
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                            ),
                            ft.Text("Relanza automáticamente la caña si no se detecta mordida en este lapso.", size=11, color=self._tokens.text_secondary),
                            self._max_wait_slider
                        ],
                        spacing=2
                    ),
                    # Switch Reintentar
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Column(
                                    controls=[
                                        ft.Text("Reintentar si se pierde el objetivo", size=12, weight=ft.FontWeight.W_500, color=self._tokens.text_primary),
                                        ft.Text("Vuelve a enfocar el anzuelo antes de pausar la sesión.", size=11, color=self._tokens.text_secondary)
                                    ],
                                    spacing=2,
                                    expand=True
                                ),
                                self._retry_switch
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                        ),
                        padding=ft.Padding.only(top=4, bottom=4)
                    ),
                    # Dropdown Errores Consecutivos
                    ft.Column(
                        controls=[
                            ft.Text("Pausar tras errores consecutivos", size=12, weight=ft.FontWeight.W_500, color=self._tokens.text_primary),
                            self._consecutive_errors_dropdown
                        ],
                        spacing=4
                    )
                ],
                spacing=14
            ),
            bgcolor=self._tokens.card_bg,
            border=ft.Border.all(1, self._tokens.card_border),
            border_radius=12,
            padding=16
        )

        # ---------------------------------------------------------------------
        # 4. BOTONES INFERIORES: RESTABLECER Y GUARDAR (Figma 72:4888)
        # ---------------------------------------------------------------------
        self._status_feedback = ft.Text(
            "Sin cambios pendientes",
            size=11.5,
            color=self._tokens.text_muted
        )

        self._reset_btn = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.RESTART_ALT_ROUNDED, size=14, color=self._tokens.text_secondary),
                    ft.Text("Restablecer", size=12, color=self._tokens.text_secondary, weight=ft.FontWeight.W_500)
                ],
                spacing=6,
                alignment=ft.MainAxisAlignment.CENTER
            ),
            bgcolor=self._tokens.sub_bg,
            border=ft.Border.all(1, self._tokens.card_border),
            border_radius=8,
            height=36,
            padding=ft.Padding.symmetric(horizontal=14),
            on_click=self._on_reset_click,
            ink=True
        )

        self._save_btn = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.CHECK_ROUNDED, size=14, color=self._tokens.text_on_primary),
                    ft.Text("Guardar perfil", size=12, color=self._tokens.text_on_primary, weight=ft.FontWeight.W_600)
                ],
                spacing=6,
                alignment=ft.MainAxisAlignment.CENTER
            ),
            bgcolor=self._tokens.primary,
            border=ft.Border.all(1, self._tokens.primary),
            border_radius=8,
            height=36,
            padding=ft.Padding.symmetric(horizontal=16),
            on_click=self._on_save_click,
            ink=True
        )

        action_bar = ft.Row(
            controls=[
                self._status_feedback,
                ft.Row(
                    controls=[self._reset_btn, self._save_btn],
                    spacing=8
                )
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER
        )

        # Layout Principal
        content_column = ft.Column(
            controls=[
                header,
                profile_card,
                detection_card,
                safety_card,
                action_bar
            ],
            spacing=16,
            scroll=ft.ScrollMode.ADAPTIVE
        )

        super().__init__(
            content=content_column,
            padding=ft.Padding.all(20),
            bgcolor=self._tokens.canvas_bg,
            border_radius=ft.BorderRadius.only(top_left=16, bottom_left=16),
            expand=True
        )

    # -------------------------------------------------------------------------
    # Callbacks y Handlers
    # -------------------------------------------------------------------------
    def _on_profile_changed(self, e: Any) -> None:
        p = self._profile_dropdown.value
        self._badge_profile_text.value = f"PERFIL: {p.upper()}"
        if p == "balanced":
            self._conf_slider.value = 85
            self._conf_badge.value = "85%"
            self._color_tol_slider.value = 20
            self._color_tol_badge.value = "20%"
            self._cast_delay_slider.value = 1500
            self._cast_delay_badge.value = "1500 ms"
        elif p == "fast":
            self._conf_slider.value = 75
            self._conf_badge.value = "75%"
            self._color_tol_slider.value = 25
            self._color_tol_badge.value = "25%"
            self._cast_delay_slider.value = 800
            self._cast_delay_badge.value = "800 ms"
        elif p == "high_precision":
            self._conf_slider.value = 92
            self._conf_badge.value = "92%"
            self._color_tol_slider.value = 12
            self._color_tol_badge.value = "12%"
            self._cast_delay_slider.value = 2200
            self._cast_delay_badge.value = "2200 ms"
        self._status_feedback.value = "Perfil modificado (Pendiente de guardar)"
        self._status_feedback.color = "#f59e0b"
        safe_update(self)

    def _on_conf_change(self, e: Any) -> None:
        self._conf_badge.value = f"{int(self._conf_slider.value)}%"
        self._mark_modified()
        safe_update(self._conf_badge)

    def _on_color_tol_change(self, e: Any) -> None:
        self._color_tol_badge.value = f"{int(self._color_tol_slider.value)}%"
        self._mark_modified()
        safe_update(self._color_tol_badge)

    def _on_cast_delay_change(self, e: Any) -> None:
        self._cast_delay_badge.value = f"{int(self._cast_delay_slider.value)} ms"
        self._mark_modified()
        safe_update(self._cast_delay_badge)

    def _on_max_wait_change(self, e: Any) -> None:
        self._max_wait_badge.value = f"{int(self._max_wait_slider.value)} s"
        self._mark_modified()
        safe_update(self._max_wait_badge)

    def _mark_modified(self) -> None:
        self._status_feedback.value = "Cambios pendientes sin guardar"
        self._status_feedback.color = "#f59e0b"
        safe_update(self._status_feedback)

    def _on_reset_click(self, e: Any) -> None:
        self._conf_slider.value = int(self._config.min_confidence * 100)
        self._conf_badge.value = f"{int(self._conf_slider.value)}%"
        self._color_tol_slider.value = int(self._config.color_tolerance * 100)
        self._color_tol_badge.value = f"{int(self._color_tol_slider.value)}%"
        self._cast_delay_slider.value = self._config.cast_delay_ms
        self._cast_delay_badge.value = f"{self._config.cast_delay_ms} ms"
        self._max_wait_slider.value = self._config.max_wait_bite_sec
        self._max_wait_badge.value = f"{self._config.max_wait_bite_sec} s"
        self._retry_switch.value = self._config.retry_on_lost
        self._consecutive_errors_dropdown.value = str(self._config.pause_on_consecutive_errors)
        self._profile_dropdown.value = self._config.profile
        self._badge_profile_text.value = f"PERFIL: {self._config.profile.upper()}"
        self._status_feedback.value = "Valores restablecidos"
        self._status_feedback.color = self._tokens.text_muted
        safe_update(self)

    def _on_save_click(self, e: Any) -> None:
        new_config = AppConfig(
            target_fps=self._config.target_fps,
            monitor_index=self._config.monitor_index,
            capture_source=self._config.capture_source,
            pause_on_defocus=self._config.pause_on_defocus,
            minimize_to_tray=self._config.minimize_to_tray,
            open_at_startup=self._config.open_at_startup,
            shortcut_toggle=self._config.shortcut_toggle,
            shortcut_stop=self._config.shortcut_stop,
            theme_mode=self._config.theme_mode,
            accent_color=self._config.accent_color,
            show_greetings=self._config.show_greetings,
            use_local_time=self._config.use_local_time,
            enable_transition_animations=self._config.enable_transition_animations,
            language=self._config.language,

            profile=self._profile_dropdown.value or "balanced",
            min_confidence=float(self._conf_slider.value) / 100.0,
            color_tolerance=float(self._color_tol_slider.value) / 100.0,
            search_area=self._search_area_dropdown.value or "fullscreen",
            cast_delay_ms=int(self._cast_delay_slider.value),
            max_wait_bite_sec=int(self._max_wait_slider.value),
            retry_on_lost=bool(self._retry_switch.value),
            pause_on_consecutive_errors=int(self._consecutive_errors_dropdown.value or 3),

            input_backend=self._config.input_backend,
            vision_strategy=self._config.vision_strategy,
            button_threshold=self._config.button_threshold,
            cache_button_size=self._config.cache_button_size,
            humanized_input=self._config.humanized_input,
            ui_theme=self._config.ui_theme,
            ui_transparency=self._config.ui_transparency,
        )
        self._config = new_config
        save_config(new_config, self._config_path)
        if self._on_save_cb:
            self._on_save_cb(new_config)

        self._status_feedback.value = "Perfil guardado correctamente"
        self._status_feedback.color = "#10b981"
        safe_update(self)

    def apply_theme(self, tokens: ThemeTokens) -> None:
        self._tokens = tokens
        self.bgcolor = tokens.canvas_bg
        self._title_text.color = tokens.text_primary
        self._subtitle_text.color = tokens.text_secondary
        self._badge_profile_text.color = tokens.primary
        self._profile_badge.bgcolor = tokens.sub_bg
        self._profile_badge.border = ft.Border.all(1, tokens.card_border)
        self._conf_badge.color = tokens.primary
        self._conf_slider.active_color = tokens.primary
        self._color_tol_badge.color = tokens.primary
        self._color_tol_slider.active_color = tokens.primary
        self._cast_delay_badge.color = tokens.primary
        self._cast_delay_slider.active_color = tokens.primary
        self._max_wait_badge.color = tokens.primary
        self._max_wait_slider.active_color = tokens.primary
        self._retry_switch.active_color = tokens.primary
        self._save_btn.bgcolor = tokens.primary
        self._save_btn.border = ft.Border.all(1, tokens.primary)
        self._reset_btn.bgcolor = tokens.sub_bg
        self._reset_btn.border = ft.Border.all(1, tokens.card_border)
        safe_update(self)
