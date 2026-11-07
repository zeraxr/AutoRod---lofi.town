"""Vista de Configuración de Sistema y Comportamiento en Flet (Diseño Oficial Figma 1:1)."""

from typing import Callable, Any
import flet as ft
from autorod.infrastructure.ui.flet.theme import ThemeManager, ThemeTokens, apply_switch_theme
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
            size=29,
            weight=ft.FontWeight.W_600,
            color="#ffffff" if self._tokens.mode == "dark" else self._tokens.text_primary
        )
        self._subtitle_text = ft.Text(
            "Todo listo para tu próxima sesión de pesca.",
            size=13,
            weight=ft.FontWeight.NORMAL,
            color="#a5b4ff" if self._tokens.mode == "dark" else self._tokens.text_secondary
        )

        # Insignia de estado según Figma 72:4478
        self._status_dot = ft.Container(width=5, height=5, border_radius=3, bgcolor="#5554d9")
        self._status_label = ft.Text("Pausado", size=10, color="#a5b4ff")
        self._status_pill = ft.Container(
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

        header = ft.Row(
            controls=[
                ft.Column(
                    controls=[self._title_text, self._subtitle_text],
                    spacing=8
                ),
                self._status_pill
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER
        )

        # ---------------------------------------------------------------------
        # 1. SECCIÓN: CAPTURA DE PANTALLA (Figma 72:4481)
        # ---------------------------------------------------------------------
        monitor_options = self._detect_monitors()
        self._monitor_dropdown = ft.Dropdown(
            options=monitor_options,
            value=str(self._config.monitor_index),
            bgcolor="#141a2a" if self._tokens.mode == "dark" else "#ffffff",
            border_color="#2a2f3a" if self._tokens.mode == "dark" else "#e5e7eb",
            focused_border_color=self._tokens.primary,
            text_size=12,
            content_padding=ft.Padding.symmetric(horizontal=12, vertical=8),
            width=200,
            height=34,
            on_select=lambda _: self._mark_modified()
        )

        self._fps_dropdown = ft.Dropdown(
            options=[
                ft.DropdownOption("30", "30 FPS"),
                ft.DropdownOption("60", "60 FPS · recomendado"),
                ft.DropdownOption("120", "120 FPS")
            ],
            value=str(self._config.target_fps),
            bgcolor="#141a2a" if self._tokens.mode == "dark" else "#ffffff",
            border_color="#2a2f3a" if self._tokens.mode == "dark" else "#e5e7eb",
            focused_border_color=self._tokens.primary,
            text_size=12,
            content_padding=ft.Padding.symmetric(horizontal=12, vertical=8),
            width=200,
            height=34,
            on_select=lambda _: self._mark_modified()
        )

        capture_card = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Column(
                        controls=[
                            ft.Text("Captura de pantalla", size=14, weight=ft.FontWeight.W_600, color="#ffffff" if self._tokens.mode == "dark" else self._tokens.text_primary),
                            ft.Text("Elige dónde buscar el objetivo de pesca.", size=11, color="#8f99b3")
                        ],
                        spacing=5
                    ),
                    ft.Row(
                        controls=[
                            ft.Column(
                                controls=[
                                    ft.Text("Pantalla de origen", size=13, color="#ffffff" if self._tokens.mode == "dark" else self._tokens.text_primary),
                                    ft.Text("1920 × 1080 · pantalla principal", size=11, color="#8f99b3")
                                ],
                                spacing=4
                            ),
                            self._monitor_dropdown
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER
                    ),
                    ft.Row(
                        controls=[
                            ft.Column(
                                controls=[
                                    ft.Text("Frecuencia de captura", size=13, color="#ffffff" if self._tokens.mode == "dark" else self._tokens.text_primary),
                                    ft.Text("Más FPS ofrecen una detección más fluida.", size=11, color="#8f99b3")
                                ],
                                spacing=4
                            ),
                            self._fps_dropdown
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER
                    ),
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.INFO_OUTLINE_ROUNDED, size=13, color="#8f99b3"),
                            ft.Text("Latencia estimada < 20 ms. La captura se activará al iniciar.", size=11, color="#8f99b3")
                        ],
                        spacing=8
                    )
                ],
                spacing=12
            ),
            bgcolor="#0d0f17" if self._tokens.mode == "dark" else "#ffffff",
            border=ft.Border.all(1, "#1b2233" if self._tokens.mode == "dark" else "#e5e7eb"),
            border_radius=12,
            padding=ft.Padding.all(16)
        )

        # ---------------------------------------------------------------------
        # 2. SECCIÓN: COMPORTAMIENTO DE LA APLICACIÓN (Figma 72:4503)
        # ---------------------------------------------------------------------
        self._defocus_switch = ft.Switch(
            value=self._config.pause_on_defocus,
            on_change=lambda _: self._mark_modified()
        )
        self._tray_switch = ft.Switch(
            value=self._config.minimize_to_tray,
            on_change=lambda _: self._mark_modified()
        )
        self._startup_switch = ft.Switch(
            value=self._config.open_at_startup,
            on_change=lambda _: self._mark_modified()
        )
        for sw in (self._defocus_switch, self._tray_switch, self._startup_switch):
            apply_switch_theme(sw, self._tokens.primary, self._tokens.mode == "dark")

        behavior_card = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("Comportamiento de la aplicación", size=14, weight=ft.FontWeight.W_600, color="#ffffff" if self._tokens.mode == "dark" else self._tokens.text_primary),
                    ft.Row(
                        controls=[
                            ft.Column(
                                controls=[
                                    ft.Text("Pausar al cambiar de ventana", size=13, color="#ffffff" if self._tokens.mode == "dark" else self._tokens.text_primary),
                                    ft.Text("Evita acciones fuera de la ventana del juego.", size=11, color="#8f99b3")
                                ],
                                spacing=4
                            ),
                            self._defocus_switch
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                    ),
                    ft.Row(
                        controls=[
                            ft.Column(
                                controls=[
                                    ft.Text("Minimizar a la bandeja", size=13, color="#ffffff" if self._tokens.mode == "dark" else self._tokens.text_primary),
                                    ft.Text("AutoRod sigue disponible en segundo plano.", size=11, color="#8f99b3")
                                ],
                                spacing=4
                            ),
                            self._tray_switch
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                    ),
                    ft.Row(
                        controls=[
                            ft.Text("Abrir al iniciar el sistema", size=13, color="#ffffff" if self._tokens.mode == "dark" else self._tokens.text_primary),
                            self._startup_switch
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                    )
                ],
                spacing=12
            ),
            bgcolor="#0d0f17" if self._tokens.mode == "dark" else "#ffffff",
            border=ft.Border.all(1, "#1b2233" if self._tokens.mode == "dark" else "#e5e7eb"),
            border_radius=12,
            padding=ft.Padding.all(16)
        )

        # ---------------------------------------------------------------------
        # 3. SECCIÓN: ATAJOS GLOBALES (Figma 72:4524)
        # ---------------------------------------------------------------------
        shortcuts_card = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Column(
                        controls=[
                            ft.Text("Atajos globales", size=14, weight=ft.FontWeight.W_600, color="#ffffff" if self._tokens.mode == "dark" else self._tokens.text_primary),
                            ft.Text("Disponibles incluso con AutoRod minimizado.", size=11, color="#8f99b3")
                        ],
                        spacing=5
                    ),
                    ft.Row(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Text("Pausar / Reanudar", size=12, color="#8f99b3"),
                                    ft.Container(
                                        content=ft.Text("Shift + Q", size=12, color="#ffffff" if self._tokens.mode == "dark" else self._tokens.text_primary),
                                        bgcolor="#141a2a" if self._tokens.mode == "dark" else "#f2f3f8",
                                        border=ft.Border.all(1, "#2a2f3a" if self._tokens.mode == "dark" else "#e5e7eb"),
                                        border_radius=6,
                                        padding=ft.Padding.symmetric(horizontal=12, vertical=6)
                                    )
                                ],
                                spacing=12,
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                expand=True
                            ),
                            ft.Row(
                                controls=[
                                    ft.Text("Cerrar AutoRod", size=12, color="#8f99b3"),
                                    ft.Container(
                                        content=ft.Text("Alt + Q", size=12, color="#ffffff" if self._tokens.mode == "dark" else self._tokens.text_primary),
                                        bgcolor="#141a2a" if self._tokens.mode == "dark" else "#f2f3f8",
                                        border=ft.Border.all(1, "#2a2f3a" if self._tokens.mode == "dark" else "#e5e7eb"),
                                        border_radius=6,
                                        padding=ft.Padding.symmetric(horizontal=12, vertical=6)
                                    )
                                ],
                                spacing=12,
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                expand=True
                            )
                        ],
                        spacing=24
                    )
                ],
                spacing=12
            ),
            bgcolor="#0d0f17" if self._tokens.mode == "dark" else "#ffffff",
            border=ft.Border.all(1, "#1b2233" if self._tokens.mode == "dark" else "#e5e7eb"),
            border_radius=12,
            padding=ft.Padding.all(16)
        )

        # ---------------------------------------------------------------------
        # 4. BOTONES INFERIORES: RESTABLECER Y GUARDAR (Figma 72:4538)
        # ---------------------------------------------------------------------
        self._status_feedback = ft.Text(
            "Sin cambios pendientes",
            size=11,
            color="#8f99b3"
        )

        self._reset_btn = ft.Container(
            content=ft.Text("Restablecer", size=12, color="#ffffff" if self._tokens.mode == "dark" else self._tokens.text_primary, weight=ft.FontWeight.NORMAL),
            bgcolor="#141a2a" if self._tokens.mode == "dark" else "#ffffff",
            border=ft.Border.all(1, "#2a2f3a" if self._tokens.mode == "dark" else "#e5e7eb"),
            border_radius=8,
            height=36,
            padding=ft.Padding.symmetric(horizontal=13),
            alignment=ft.Alignment(0, 0),
            on_click=self._on_reset_click,
            ink=True
        )

        self._save_btn = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.CHECK, size=14, color="#ffffff"),
                    ft.Text("Guardar cambios", size=12, color="#ffffff", weight=ft.FontWeight.NORMAL)
                ],
                spacing=8,
                alignment=ft.MainAxisAlignment.CENTER
            ),
            bgcolor="#5554d9",
            border=ft.Border.all(1, "#5554d9"),
            border_radius=8,
            height=36,
            padding=ft.Padding.symmetric(horizontal=13),
            on_click=self._on_save_click,
            ink=True
        )

        action_bar = ft.Row(
            controls=[
                self._status_feedback,
                ft.Row(
                    controls=[self._reset_btn, self._save_btn],
                    spacing=10
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
            padding=ft.Padding.only(left=32, right=32, top=48, bottom=28),
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
        safe_update(self._status_pill)

    def apply_theme(self, tokens: ThemeTokens) -> None:
        self._tokens = tokens
        self.bgcolor = tokens.canvas_bg
        self._title_text.color = tokens.text_primary
        self._subtitle_text.color = tokens.text_secondary
        for sw in (self._defocus_switch, self._tray_switch, self._startup_switch):
            apply_switch_theme(sw, tokens.primary, tokens.mode == "dark")
        self._save_btn.bgcolor = tokens.primary
        self._save_btn.border = ft.Border.all(1, tokens.primary)
        self._reset_btn.bgcolor = tokens.sub_bg
        self._reset_btn.border = ft.Border.all(1, tokens.card_border)
        safe_update(self)
