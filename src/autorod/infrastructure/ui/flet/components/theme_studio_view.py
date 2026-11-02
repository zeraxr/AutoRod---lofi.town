"""Vista de Estudio de Personalización Visual en Flet (Diseño Oficial Figma 1:1)."""

from typing import Callable, Any
import flet as ft
from autorod.infrastructure.ui.flet.theme import (
    ThemeManager,
    ThemeTokens,
    FIGMA_ACCENT_COLORS,
    DEFAULT_ACCENT,
    ThemeMode
)
from autorod.config import AppConfig, save_config
from autorod.infrastructure.ui.flet.utils import safe_update


class FletThemePreviewCard(ft.Container):
    """Tarjeta visual de selección de modo base (Oscuro, Claro, Sistema) con mockup miniatura."""

    def __init__(
        self,
        mode_id: str,
        name: str,
        is_active: bool,
        tokens: ThemeTokens,
        on_select: Callable[[str], None]
    ) -> None:
        self.mode_id = mode_id
        self._is_active = is_active
        self._tokens = tokens
        self._on_select = on_select

        # Mockup en miniatura del diseño Figma
        if mode_id == "dark":
            mini_sidebar_bg = "#1a1b26"
            mini_canvas_bg = "#11151f"
            mini_card_bg = "#0d0f17"
            mini_bar_bg = "#5554d9"
            mockup_content = ft.Row(
                controls=[
                    ft.Container(width=16, bgcolor=mini_sidebar_bg, border_radius=ft.BorderRadius.only(top_left=6, bottom_left=6)),
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Container(height=4, width=32, bgcolor=mini_bar_bg, border_radius=2),
                                ft.Container(height=16, bgcolor=mini_card_bg, border_radius=3, expand=True)
                            ],
                            spacing=4
                        ),
                        bgcolor=mini_canvas_bg,
                        padding=6,
                        expand=True,
                        border_radius=ft.BorderRadius.only(top_right=6, bottom_right=6)
                    )
                ],
                spacing=0,
                expand=True
            )
        elif mode_id == "light":
            mini_sidebar_bg = "#dadde9"
            mini_canvas_bg = "#f2f3f8"
            mini_card_bg = "#ffffff"
            mini_bar_bg = "#5554d9"
            mockup_content = ft.Row(
                controls=[
                    ft.Container(width=16, bgcolor=mini_sidebar_bg, border_radius=ft.BorderRadius.only(top_left=6, bottom_left=6)),
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Container(height=4, width=32, bgcolor=mini_bar_bg, border_radius=2),
                                ft.Container(height=16, bgcolor=mini_card_bg, border_radius=3, expand=True)
                            ],
                            spacing=4
                        ),
                        bgcolor=mini_canvas_bg,
                        padding=6,
                        expand=True,
                        border_radius=ft.BorderRadius.only(top_right=6, bottom_right=6)
                    )
                ],
                spacing=0,
                expand=True
            )
        else: # Sistema (dividido 50/50)
            mockup_content = ft.Row(
                controls=[
                    ft.Container(
                        bgcolor="#11151f",
                        expand=True,
                        border_radius=ft.BorderRadius.only(top_left=6, bottom_left=6)
                    ),
                    ft.Container(
                        bgcolor="#f2f3f8",
                        expand=True,
                        border_radius=ft.BorderRadius.only(top_right=6, bottom_right=6)
                    )
                ],
                spacing=0,
                expand=True
            )

        self._mockup_box = ft.Container(
            content=mockup_content,
            height=60,
            border_radius=6,
            border=ft.Border.all(1, "#2a2f3a" if mode_id != "light" else "#e5e7eb")
        )

        self._check_icon = ft.Icon(
            ft.Icons.CHECK_CIRCLE_ROUNDED,
            size=14,
            color=self._tokens.primary,
            visible=is_active
        )
        self._name_text = ft.Text(
            name,
            size=12.5,
            weight=ft.FontWeight.BOLD if is_active else ft.FontWeight.W_500,
            color=self._tokens.text_primary
        )

        super().__init__(
            content=ft.Column(
                controls=[
                    self._mockup_box,
                    ft.Row(
                        controls=[self._name_text, self._check_icon],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                    )
                ],
                spacing=8
            ),
            bgcolor=self._tokens.sub_bg if is_active else self._tokens.card_bg,
            border=ft.Border.all(1.5 if is_active else 1, self._tokens.primary if is_active else self._tokens.card_border),
            border_radius=10,
            padding=10,
            expand=True,
            on_click=lambda _: self._on_select(self.mode_id),
            ink=True
        )

    def set_active(self, active: bool, primary_color: str) -> None:
        self._is_active = active
        self._check_icon.visible = active
        self._check_icon.color = primary_color
        self._name_text.weight = ft.FontWeight.BOLD if active else ft.FontWeight.W_500
        self.border = ft.Border.all(1.5 if active else 1, primary_color if active else self._tokens.card_border)
        safe_update(self)


class FletThemeStudioView(ft.Container):
    """
    Vista de personalización visual oficial de Figma:
    - Modos de tema: Oscuro, Claro, Sistema.
    - 6 Colores de acento Tokyo Night / SOTA (#0f141d, #5554d9, #7aa2f7, #7dcfff, #9ece6a, #f7768e).
    - Checklist de rendimiento y animaciones: Saludos, Hora local, Animaciones de transición.
    - Selector de Idioma: Español / English.
    - Acciones de Guardar y Restablecer.
    """

    def __init__(
        self,
        config: AppConfig,
        config_path: str = "config.toml",
        theme_manager: ThemeManager | None = None,
        on_preferences_changed: Callable[[dict[str, Any]], None] | None = None
    ) -> None:
        self._config = config
        self._config_path = config_path
        self._theme_mgr = theme_manager or ThemeManager.get_instance()
        self._tokens: ThemeTokens = self._theme_mgr.current
        self._on_prefs_changed = on_preferences_changed

        self._active_mode = getattr(config, "theme_mode", "dark")
        self._active_accent = getattr(config, "accent_color", DEFAULT_ACCENT)

        # ---------------------------------------------------------------------
        # 0. HEADER PRINCIPAL (Figma 72:4547)
        # ---------------------------------------------------------------------
        self._title_text = ft.Text(
            "Personalización",
            size=26,
            weight=ft.FontWeight.W_700,
            color=self._tokens.text_primary
        )
        self._subtitle_text = ft.Text(
            "Apariencia visual, paleta de colores e interactividad.",
            size=12,
            color=self._tokens.text_secondary
        )

        self._active_badge_text = ft.Text(
            f"TEMA: {self._active_mode.upper()}",
            size=10,
            weight=ft.FontWeight.W_700,
            color=self._tokens.primary
        )
        self._active_badge = ft.Container(
            content=self._active_badge_text,
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
                self._active_badge
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER
        )

        # ---------------------------------------------------------------------
        # 1. SECCIÓN: TEMA DE LA APLICACIÓN (Figma 72:4547)
        # ---------------------------------------------------------------------
        self._theme_cards: dict[str, FletThemePreviewCard] = {}
        for mid, mname in [("dark", "Oscuro"), ("light", "Claro"), ("system", "Sistema")]:
            card = FletThemePreviewCard(
                mode_id=mid,
                name=mname,
                is_active=(mid == self._active_mode),
                tokens=self._tokens,
                on_select=self._on_mode_select
            )
            self._theme_cards[mid] = card

        # Compatibilidad para tests unitarios
        self._cards = list(self._theme_cards.values())

        theme_mode_card = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.BRIGHTNESS_6_ROUNDED, size=16, color=self._tokens.primary),
                            ft.Text("Tema de la aplicación", size=14, weight=ft.FontWeight.W_600, color=self._tokens.text_primary)
                        ],
                        spacing=8
                    ),
                    ft.Text(
                        "Selecciona la paleta estructural de la interfaz entre contraste profundo, claridad o seguimiento automático del sistema.",
                        size=11.5,
                        color=self._tokens.text_secondary
                    ),
                    ft.Row(
                        controls=list(self._theme_cards.values()),
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
        # 2. SECCIÓN: COLOR DE ACENTO (6 Swatches de Figma 72:4547)
        # ---------------------------------------------------------------------
        self._swatch_containers: dict[str, ft.Container] = {}
        swatch_controls: list[ft.Container] = []

        for hex_code, label in FIGMA_ACCENT_COLORS:
            is_active = (hex_code.lower() == self._active_accent.lower())
            ring = ft.Container(
                content=ft.Container(
                    width=22,
                    height=22,
                    border_radius=11,
                    bgcolor=hex_code,
                    content=ft.Icon(ft.Icons.CHECK, size=14, color="#ffffff" if hex_code != "#ffffff" else "#000000", visible=is_active)
                ),
                width=34,
                height=34,
                border_radius=17,
                border=ft.Border.all(2, self._tokens.primary if is_active else ft.Colors.TRANSPARENT),
                alignment=ft.Alignment(0, 0),
                tooltip=f"{label} ({hex_code})",
                on_click=lambda _, h=hex_code: self._on_accent_select(h),
                ink=True
            )
            self._swatch_containers[hex_code] = ring
            swatch_controls.append(ring)

        accent_card = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.PALETTE_ROUNDED, size=16, color=self._tokens.primary),
                            ft.Text("Color de acento", size=14, weight=ft.FontWeight.W_600, color=self._tokens.text_primary)
                        ],
                        spacing=8
                    ),
                    ft.Text(
                        "Afecta exclusivamente el botón 'Iniciar' (relleno), 'Pausar' (contorno), gráficas y elementos destacados.",
                        size=11.5,
                        color=self._tokens.text_secondary
                    ),
                    ft.Row(
                        controls=swatch_controls,
                        spacing=10
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
        # 3. SECCIÓN: COMPORTAMIENTO DE LA INTERFAZ (CHECKLIST)
        # ---------------------------------------------------------------------
        self._chk_greetings = ft.Checkbox(
            label="saludos",
            value=getattr(self._config, "show_greetings", True),
            active_color=self._tokens.primary,
            on_change=self._on_behavior_toggled
        )
        self._chk_local_time = ft.Checkbox(
            label="hora local",
            value=getattr(self._config, "use_local_time", True),
            active_color=self._tokens.primary,
            on_change=self._on_behavior_toggled
        )
        self._chk_animations = ft.Checkbox(
            label="animaciones de transición",
            value=getattr(self._config, "enable_transition_animations", True),
            active_color=self._tokens.primary,
            on_change=self._on_behavior_toggled
        )

        # Aliases para compatibilidad
        self._chk_saludos = self._chk_greetings
        self._chk_hora_local = self._chk_local_time
        self._chk_animaciones = self._chk_animations

        checklist_card = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.CHECKLIST_ROUNDED, size=16, color=self._tokens.primary),
                            ft.Text("Comportamiento y Animaciones", size=14, weight=ft.FontWeight.W_600, color=self._tokens.text_primary)
                        ],
                        spacing=8
                    ),
                    ft.Text(
                        "Personaliza qué componentes visuales se muestran y desactiva animaciones si buscas rendimiento ultra-ligero.",
                        size=11.5,
                        color=self._tokens.text_secondary
                    ),
                    ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    self._chk_greetings,
                                    ft.Text("Muestra mensajes cordiales y frases de ánimo estilo Minecraft.", size=11, color=self._tokens.text_secondary)
                                ],
                                spacing=8
                            ),
                            ft.Row(
                                controls=[
                                    self._chk_local_time,
                                    ft.Text("Sincroniza los saludos con la hora de tu reloj ('Buenos días', 'Buenas tardes', 'Buenas noches').", size=11, color=self._tokens.text_secondary)
                                ],
                                spacing=8
                            ),
                            ft.Row(
                                controls=[
                                    self._chk_animations,
                                    ft.Text("Transiciones cinéticas al alternar entre pantallas.", size=11, color=self._tokens.text_secondary)
                                ],
                                spacing=8
                            )
                        ],
                        spacing=6
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
        # 4. SECCIÓN: IDIOMA (Figma 72:4547)
        # ---------------------------------------------------------------------
        self._lang_dropdown = ft.Dropdown(
            options=[
                ft.DropdownOption("es", "Español (Latinoamérica)"),
                ft.DropdownOption("en", "English (United States)")
            ],
            value=getattr(self._config, "language", "es"),
            bgcolor=self._tokens.card_bg,
            border_color=self._tokens.card_border,
            focused_border_color=self._tokens.primary,
            text_size=12,
            content_padding=ft.Padding.symmetric(horizontal=12, vertical=8),
            on_select=lambda _: self._mark_modified()
        )

        lang_card = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.LANGUAGE_ROUNDED, size=16, color=self._tokens.primary),
                            ft.Text("Idioma de la Aplicación", size=14, weight=ft.FontWeight.W_600, color=self._tokens.text_primary)
                        ],
                        spacing=8
                    ),
                    self._lang_dropdown
                ],
                spacing=10
            ),
            bgcolor=self._tokens.card_bg,
            border=ft.Border.all(1, self._tokens.card_border),
            border_radius=12,
            padding=16
        )

        # ---------------------------------------------------------------------
        # 5. BOTONES INFERIORES: RESTABLECER Y GUARDAR (Figma 72:4547)
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
                theme_mode_card,
                accent_card,
                checklist_card,
                lang_card,
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

    def _on_mode_select(self, mode: str) -> None:
        self._active_mode = mode
        self._theme_mgr.set_theme_mode(mode)
        self._tokens = self._theme_mgr.current
        for mid, card in self._theme_cards.items():
            card.set_active(mid == mode, self._tokens.primary)
        self._active_badge_text.value = f"TEMA: {mode.upper()}"
        self._mark_modified()
        if self._on_prefs_changed:
            self._on_prefs_changed({
                "theme_mode": self._active_mode,
                "accent_color": self._active_accent,
                "show_greetings": self._chk_greetings.value,
                "use_local_time": self._chk_local_time.value,
                "enable_transition_animations": self._chk_animations.value
            })
        safe_update(self)

    def _on_accent_select(self, hex_code: str) -> None:
        self._active_accent = hex_code
        self._theme_mgr.set_accent_color(hex_code)
        self._tokens = self._theme_mgr.current
        for h, ring in self._swatch_containers.items():
            active = (h.lower() == hex_code.lower())
            ring.border = ft.Border.all(2, hex_code if active else ft.Colors.TRANSPARENT)
            ring.content.content.visible = active
        self._mark_modified()
        if self._on_prefs_changed:
            self._on_prefs_changed({
                "theme_mode": self._active_mode,
                "accent_color": self._active_accent,
                "show_greetings": self._chk_greetings.value,
                "use_local_time": self._chk_local_time.value,
                "enable_transition_animations": self._chk_animations.value
            })
        safe_update(self)

    def _on_behavior_toggled(self, e: Any) -> None:
        self._mark_modified()
        if self._on_prefs_changed:
            self._on_prefs_changed({
                "theme_mode": self._active_mode,
                "accent_color": self._active_accent,
                "show_greetings": self._chk_greetings.value,
                "use_local_time": self._chk_local_time.value,
                "enable_transition_animations": self._chk_animations.value
            })

    def _mark_modified(self) -> None:
        self._status_feedback.value = "Cambios pendientes sin guardar"
        self._status_feedback.color = "#f59e0b"
        safe_update(self._status_feedback)

    def _on_reset_click(self, e: Any) -> None:
        self._active_mode = getattr(self._config, "theme_mode", "dark")
        self._active_accent = getattr(self._config, "accent_color", DEFAULT_ACCENT)
        self._chk_greetings.value = getattr(self._config, "show_greetings", True)
        self._chk_local_time.value = getattr(self._config, "use_local_time", True)
        self._chk_animations.value = getattr(self._config, "enable_transition_animations", True)
        self._lang_dropdown.value = getattr(self._config, "language", "es")

        self._theme_mgr.set_theme_mode(self._active_mode)
        self._theme_mgr.set_accent_color(self._active_accent)
        self._tokens = self._theme_mgr.current

        for mid, card in self._theme_cards.items():
            card.set_active(mid == self._active_mode, self._tokens.primary)
        for h, ring in self._swatch_containers.items():
            active = (h.lower() == self._active_accent.lower())
            ring.border = ft.Border.all(2, h if active else ft.Colors.TRANSPARENT)
            ring.content.content.visible = active

        self._active_badge_text.value = f"TEMA: {self._active_mode.upper()}"
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

            theme_mode=self._active_mode,
            accent_color=self._active_accent,
            show_greetings=bool(self._chk_greetings.value),
            use_local_time=bool(self._chk_local_time.value),
            enable_transition_animations=bool(self._chk_animations.value),
            language=self._lang_dropdown.value or "es",

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

        self._status_feedback.value = "Personalización guardada correctamente"
        self._status_feedback.color = "#10b981"
        safe_update(self)

    def apply_theme(self, tokens: ThemeTokens) -> None:
        self._tokens = tokens
        self.bgcolor = tokens.canvas_bg
        self._title_text.color = tokens.text_primary
        self._subtitle_text.color = tokens.text_secondary
        self._save_btn.bgcolor = tokens.primary
        self._save_btn.border = ft.Border.all(1, tokens.primary)
        self._reset_btn.bgcolor = tokens.sub_bg
        self._reset_btn.border = ft.Border.all(1, tokens.card_border)
        safe_update(self)
