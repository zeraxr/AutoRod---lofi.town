"""Vista de Configuración de Sistema y Comportamiento en Flet (Diseño Oficial Figma 1:1)."""

from typing import Callable, Any
import flet as ft
from autorod.infrastructure.ui.flet.theme import ThemeManager, ThemeTokens
from autorod.config import AppConfig, save_config
from autorod.infrastructure.ui.flet.utils import safe_update
import mss


class FletSettingsView(ft.Container):
    """
    Panel de configuración de captura de pantalla, comportamiento de ventana y atajos de teclado globales.
    Estrictamente alineado 1:1 con Figma (Frames 72:4389 Modo Oscuro y 78:128 Modo Claro).
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
        # 0. HEADER PRINCIPAL (Figma 72:4389)
        # ---------------------------------------------------------------------
        self._title_text = ft.Text(
            "Configuración",
            size=26,
            weight=ft.FontWeight.W_700,
            color=self._tokens.text_primary
        )
        self._subtitle_text = ft.Text(
            "Ajustes del sistema y comportamiento de la aplicación.",
            size=12,
            color=self._tokens.text_secondary
        )

        header = ft.Row(
            controls=[
                ft.Column(
                    controls=[self._title_text, self._subtitle_text],
                    spacing=2
                ),
                ft.Container(
                    content=ft.Text(
                        "CONFIG.TOML",
                        style=ft.TextStyle(
                            size=10,
                            weight=ft.FontWeight.W_700,
                            color=self._tokens.primary,
                            letter_spacing=0.5
                        )
                    ),
                    bgcolor=self._tokens.sub_bg,
                    border=ft.Border.all(1, self._tokens.card_border),
                    border_radius=6,
                    padding=ft.Padding.symmetric(horizontal=10, vertical=6)
                )
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER
        )

        # ---------------------------------------------------------------------
        # 1. SECCIÓN: CAPTURA Y PANTALLA (Figma 72:4389)
        # ---------------------------------------------------------------------
        monitor_options = self._detect_monitors()
        self._monitor_dropdown = ft.Dropdown(
            options=monitor_options,
            value=str(self._config.monitor_index),
            bgcolor=self._tokens.card_bg,
            border_color=self._tokens.card_border,
            focused_border_color=self._tokens.primary,
            text_size=12,
            content_padding=ft.Padding.symmetric(horizontal=12, vertical=8),
            expand=True,
            on_select=lambda _: self._mark_modified()
        )

        self._fps_dropdown = ft.Dropdown(
            options=[
                ft.DropdownOption("30", "30 FPS (Ahorro de recursos)"),
                ft.DropdownOption("60", "60 FPS (Recomendado - Fluidez SOTA)"),
                ft.DropdownOption("120", "120 FPS (Máxima precisión)")
            ],
            value=str(self._config.target_fps),
            bgcolor=self._tokens.card_bg,
            border_color=self._tokens.card_border,
            focused_border_color=self._tokens.primary,
            text_size=12,
            content_padding=ft.Padding.symmetric(horizontal=12, vertical=8),
            expand=True,
            on_select=lambda _: self._mark_modified()
        )

        capture_card = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.DESKTOP_WINDOWS_ROUNDED, size=16, color=self._tokens.primary),
                            ft.Text("Captura y Pantalla", size=14, weight=ft.FontWeight.W_600, color=self._tokens.text_primary)
                        ],
                        spacing=8
                    ),
                    ft.Row(
                        controls=[
                            ft.Column(
                                controls=[
                                    ft.Text("Pantalla de origen", size=12, weight=ft.FontWeight.W_500, color=self._tokens.text_primary),
                                    ft.Text("Monitor donde se ejecuta el juego.", size=11, color=self._tokens.text_secondary),
                                    self._monitor_dropdown
                                ],
                                spacing=4,
                                expand=True
                            ),
                            ft.Column(
                                controls=[
                                    ft.Text("Frecuencia de captura", size=12, weight=ft.FontWeight.W_500, color=self._tokens.text_primary),
                                    ft.Text("Tasa de fotogramas procesados.", size=11, color=self._tokens.text_secondary),
                                    self._fps_dropdown
                                ],
                                spacing=4,
                                expand=True
                            )
                        ],
                        spacing=16
                    )
                ],
                spacing=12
            ),
            bgcolor=self._tokens.card_bg,
            border=ft.Border.all(1, self._tokens.card_border),
            border_radius=12,
            padding=16
        )

        # ---------------------------------------------------------------------
        # 2. SECCIÓN: COMPORTAMIENTO (Figma 72:4389)
        # ---------------------------------------------------------------------
        self._defocus_switch = ft.Switch(
            value=self._config.pause_on_defocus,
            active_color=self._tokens.primary,
            scale=0.85,
            on_change=lambda _: self._mark_modified()
        )
        self._tray_switch = ft.Switch(
            value=self._config.minimize_to_tray,
            active_color=self._tokens.primary,
            scale=0.85,
            on_change=lambda _: self._mark_modified()
        )
        self._startup_switch = ft.Switch(
            value=self._config.open_at_startup,
            active_color=self._tokens.primary,
            scale=0.85,
            on_change=lambda _: self._mark_modified()
        )

        def _create_switch_row(title: str, subtitle: str, switch_ctrl: ft.Switch) -> ft.Container:
            return ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Column(
                            controls=[
                                ft.Text(title, size=12.5, weight=ft.FontWeight.W_500, color=self._tokens.text_primary),
                                ft.Text(subtitle, size=11, color=self._tokens.text_secondary)
                            ],
                            spacing=2,
                            expand=True
                        ),
                        switch_ctrl
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                ),
                padding=ft.Padding.symmetric(vertical=4)
            )

        behavior_card = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.TUNE_ROUNDED, size=16, color=self._tokens.primary),
                            ft.Text("Comportamiento", size=14, weight=ft.FontWeight.W_600, color=self._tokens.text_primary)
                        ],
                        spacing=8
                    ),
                    _create_switch_row(
                        "Pausar al cambiar de ventana",
                        "Detiene la detección si AutoRod o el juego pierden el foco principal.",
                        self._defocus_switch
                    ),
                    ft.Divider(height=1, color=self._tokens.divider),
                    _create_switch_row(
                        "Minimizar a la bandeja del sistema",
                        "Al minimizar, la aplicación continúa ejecutándose en el área de notificación.",
                        self._tray_switch
                    ),
                    ft.Divider(height=1, color=self._tokens.divider),
                    _create_switch_row(
                        "Abrir al iniciar el sistema",
                        "Inicia AutoRod minimizado automáticamente al encender Windows.",
                        self._startup_switch
                    ),
                ],
                spacing=8
            ),
            bgcolor=self._tokens.card_bg,
            border=ft.Border.all(1, self._tokens.card_border),
            border_radius=12,
            padding=16
        )

        # ---------------------------------------------------------------------
        # 3. SECCIÓN: ATAJOS DE TECLADO GLOBALES (Figma 72:4389)
        # ---------------------------------------------------------------------
        def _create_shortcut_card(title: str, subtitle: str, key_badge: str) -> ft.Container:
            return ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Column(
                            controls=[
                                ft.Text(title, size=12.5, weight=ft.FontWeight.W_500, color=self._tokens.text_primary),
                                ft.Text(subtitle, size=11, color=self._tokens.text_secondary)
                            ],
                            spacing=2,
                            expand=True
                        ),
                        ft.Container(
                            content=ft.Text(key_badge, size=11.5, weight=ft.FontWeight.BOLD, color=self._tokens.primary),
                            bgcolor=self._tokens.sub_bg,
                            border=ft.Border.all(1, self._tokens.card_border),
                            border_radius=6,
                            padding=ft.Padding.symmetric(horizontal=12, vertical=6)
                        )
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER
                ),
                bgcolor=self._tokens.card_bg,
                border=ft.Border.all(1, self._tokens.card_border),
                border_radius=10,
                padding=12,
                expand=True
            )

        shortcuts_card = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.KEYBOARD_ROUNDED, size=16, color=self._tokens.primary),
                            ft.Text("Atajos de Teclado Globales", size=14, weight=ft.FontWeight.W_600, color=self._tokens.text_primary)
                        ],
                        spacing=8
                    ),
                    ft.Row(
                        controls=[
                            _create_shortcut_card("Iniciar / Pausar", "Alterna la sesión activa sin cambiar de ventana.", self._config.shortcut_toggle),
                            _create_shortcut_card("Detener sesión", "Finaliza la sesión actual y resetea contadores.", self._config.shortcut_stop)
                        ],
                        spacing=12
                    )
                ],
                spacing=12
            ),
            bgcolor=self._tokens.card_bg,
            border=ft.Border.all(1, self._tokens.card_border),
            border_radius=12,
            padding=16
        )

        # ---------------------------------------------------------------------
        # 4. BOTONES INFERIORES: RESTABLECER Y GUARDAR (Figma 72:4389)
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
                    ft.Text("Guardar cambios", size=12, color=self._tokens.text_on_primary, weight=ft.FontWeight.W_600)
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

        content_column = ft.Column(
            controls=[
                header,
                capture_card,
                behavior_card,
                shortcuts_card,
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

    def _detect_monitors(self) -> list[ft.DropdownOption]:
        options = []
        try:
            with mss.MSS() as sct:
                # sct.monitors[0] es la pantalla combinada 'All Monitors', los individuales empiezan en index 1
                for idx, m in enumerate(sct.monitors[1:], start=1):
                    options.append(ft.DropdownOption(str(idx), f"Monitor {idx} ({m['width']}x{m['height']})"))
        except Exception:
            options = [
                ft.DropdownOption("1", "Monitor 1 (Principal)"),
                ft.DropdownOption("2", "Monitor 2 (Secundario)")
            ]
        return options or [ft.DropdownOption("1", "Monitor 1")]

    def _mark_modified(self) -> None:
        self._status_feedback.value = "Cambios pendientes sin guardar"
        self._status_feedback.color = "#f59e0b"
        safe_update(self._status_feedback)

    def _on_reset_click(self, e: Any) -> None:
        self._monitor_dropdown.value = str(self._config.monitor_index)
        self._fps_dropdown.value = str(self._config.target_fps)
        self._defocus_switch.value = self._config.pause_on_defocus
        self._tray_switch.value = self._config.minimize_to_tray
        self._startup_switch.value = self._config.open_at_startup
        self._status_feedback.value = "Valores restablecidos"
        self._status_feedback.color = self._tokens.text_muted
        safe_update(self)

    def _on_save_click(self, e: Any) -> None:
        new_config = AppConfig(
            target_fps=int(self._fps_dropdown.value or 60),
            monitor_index=int(self._monitor_dropdown.value or 1),
            capture_source=self._config.capture_source,
            pause_on_defocus=bool(self._defocus_switch.value),
            minimize_to_tray=bool(self._tray_switch.value),
            open_at_startup=bool(self._startup_switch.value),
            shortcut_toggle=self._config.shortcut_toggle,
            shortcut_stop=self._config.shortcut_stop,
            theme_mode=self._config.theme_mode,
            accent_color=self._config.accent_color,
            show_greetings=self._config.show_greetings,
            use_local_time=self._config.use_local_time,
            enable_transition_animations=self._config.enable_transition_animations,
            language=self._config.language,

            profile=self._config.profile,
            min_confidence=self._config.min_confidence,
            color_tolerance=self._config.color_tolerance,
            search_area=self._config.search_area,
            cast_delay_ms=self._config.cast_delay_ms,
            max_wait_bite_sec=self._config.max_wait_bite_sec,
            retry_on_lost=self._config.retry_on_lost,
            pause_on_consecutive_errors=self._config.pause_on_consecutive_errors,

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

        self._status_feedback.value = "Configuración guardada correctamente"
        self._status_feedback.color = "#10b981"
        safe_update(self)

    def apply_theme(self, tokens: ThemeTokens) -> None:
        self._tokens = tokens
        self.bgcolor = tokens.canvas_bg
        self._title_text.color = tokens.text_primary
        self._subtitle_text.color = tokens.text_secondary
        self._defocus_switch.active_color = tokens.primary
        self._tray_switch.active_color = tokens.primary
        self._startup_switch.active_color = tokens.primary
        self._save_btn.bgcolor = tokens.primary
        self._save_btn.border = ft.Border.all(1, tokens.primary)
        self._reset_btn.bgcolor = tokens.sub_bg
        self._reset_btn.border = ft.Border.all(1, tokens.card_border)
        safe_update(self)
