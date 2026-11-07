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
    """Tarjeta visual de selección de modo base (Oscuro, Claro, Sistema) con mockup miniatura oficial de Figma."""

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

        # Mockup en miniatura del diseño Figma (h-88px, radius-8px, p-10px)
        if mode_id == "dark":
            mini_sidebar_bg = "#1a1b26"
            mini_canvas_bg = "#11151f"
            mini_card_bg = "#141a2a"
            mini_bar_bg = "#5554d9"
            mockup_content = ft.Row(
                controls=[
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Container(height=4, width=20, bgcolor="#5554d9", border_radius=2),
                                ft.Container(height=4, width=20, bgcolor="#8f99b3", border_radius=2),
                                ft.Container(height=4, width=20, bgcolor="#8f99b3", border_radius=2),
                            ],
                            spacing=6
                        ),
                        width=30,
                        bgcolor=mini_sidebar_bg,
                        padding=5,
                        border_radius=4
                    ),
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Container(height=5, width=45, bgcolor="#a5b4ff", border_radius=2),
                                ft.Container(height=31, bgcolor=mini_card_bg, border_radius=4, expand=True),
                                ft.Container(height=8, width=29, bgcolor=mini_bar_bg, border_radius=2)
                            ],
                            spacing=8
                        ),
                        bgcolor=mini_canvas_bg,
                        padding=ft.Padding.only(left=8, top=4, right=8, bottom=4),
                        expand=True,
                        border_radius=4
                    )
                ],
                spacing=8,
                expand=True
            )
        elif mode_id == "light":
            mini_sidebar_bg = "#dadde9"
            mini_canvas_bg = "#f2f3f8"
            mini_card_bg = "#ffffff"
            mini_bar_bg = "#5554d9"
            mockup_content = ft.Row(
                controls=[
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Container(height=4, width=20, bgcolor="#5554d9", border_radius=2),
                                ft.Container(height=4, width=20, bgcolor="#8f99b3", border_radius=2),
                                ft.Container(height=4, width=20, bgcolor="#8f99b3", border_radius=2),
                            ],
                            spacing=6
                        ),
                        width=30,
                        bgcolor=mini_sidebar_bg,
                        padding=5,
                        border_radius=4
                    ),
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Container(height=5, width=45, bgcolor="#55596f", border_radius=2),
                                ft.Container(height=31, bgcolor=mini_card_bg, border_radius=4, expand=True),
                                ft.Container(height=8, width=29, bgcolor=mini_bar_bg, border_radius=2)
                            ],
                            spacing=8
                        ),
                        bgcolor=mini_canvas_bg,
                        padding=ft.Padding.only(left=8, top=4, right=8, bottom=4),
                        expand=True,
                        border_radius=4
                    )
                ],
                spacing=8,
                expand=True
            )
        else:  # Sistema
            mockup_content = ft.Row(
                controls=[
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Container(height=4, width=20, bgcolor="#5554d9", border_radius=2),
                                ft.Container(height=4, width=20, bgcolor="#8f99b3", border_radius=2),
                                ft.Container(height=4, width=20, bgcolor="#8f99b3", border_radius=2),
                            ],
                            spacing=6
                        ),
                        width=30,
                        bgcolor="#1a1b26",
                        padding=5,
                        border_radius=4
                    ),
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Container(height=5, width=45, bgcolor="#a5b4ff", border_radius=2),
                                ft.Container(height=31, bgcolor="#141a2a", border_radius=4, expand=True),
                                ft.Container(height=8, width=29, bgcolor="#5554d9", border_radius=2)
                            ],
                            spacing=8
                        ),
                        bgcolor="#11151f",
                        padding=ft.Padding.only(left=8, top=4, right=8, bottom=4),
                        expand=True,
                        border_radius=4
                    )
                ],
                spacing=8,
                expand=True
            )

        box_bg = "#11151f" if mode_id != "light" else "#f2f3f8"
        box_border = "#5554d9" if is_active else ("#2a2f3a" if mode_id != "light" else "#2a2f3a")
        self._mockup_box = ft.Container(
            content=mockup_content,
            height=88,
            border_radius=8,
            padding=10,
            bgcolor=box_bg,
            border=ft.Border.all(2 if is_active else 1, box_border)
        )

        self._check_icon = ft.Icon(
            ft.Icons.CHECK_CIRCLE_ROUNDED,
            size=14,
            color=self._tokens.primary,
            visible=is_active
        )
        self._name_text = ft.Text(
            name,
            size=12,
            weight=ft.FontWeight.NORMAL,
            color="#ffffff" if is_active else "#8f99b3"
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
                spacing=10
            ),
            expand=True,
            on_click=lambda _: self._on_select(self.mode_id),
            ink=True
        )

    def set_active(self, active: bool, primary_color: str) -> None:
        self._is_active = active
        self._check_icon.visible = active
        self._check_icon.color = primary_color
        self._name_text.color = "#ffffff" if active else "#8f99b3"
        self._mockup_box.border = ft.Border.all(2 if active else 1, primary_color if active else "#2a2f3a")
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
            size=29,
            weight=ft.FontWeight.W_600,
            color="#ffffff" if self._tokens.mode == "dark" else self._tokens.text_primary
        )
        self._subtitle_text = ft.Text(
            "Tu espacio de pesca, a tu manera.",
            size=13,
            weight=ft.FontWeight.NORMAL,
            color="#a5b4ff" if self._tokens.mode == "dark" else self._tokens.text_secondary
        )

        header = ft.Row(
            controls=[
                ft.Column(
                    controls=[self._title_text, self._subtitle_text],
                    spacing=8
                )
            ],
            alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.CENTER
        )

        # ---------------------------------------------------------------------
        # 1. SECCIÓN: APARIENCIA (Temas + Color de Acento Figma 72:4636)
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

        self._cards = list(self._theme_cards.values())

        # 6 Swatches de color de acento circular (26x26, rounded-20px)
        self._swatch_containers: dict[str, ft.Container] = {}
        swatch_controls: list[ft.Container] = []

        for hex_code, label in FIGMA_ACCENT_COLORS:
            is_active = (hex_code.lower() == self._active_accent.lower())
            ring = ft.Container(
                content=ft.Icon(
                    ft.Icons.CHECK,
                    size=13,
                    color="#ffffff" if hex_code != "#ffffff" else "#000000",
                    visible=is_active
                ),
                width=26,
                height=26,
                border_radius=20,
                bgcolor=hex_code,
                border=ft.Border.all(2, "#ffffff") if is_active else None,
                alignment=ft.Alignment(0, 0),
                tooltip=f"{label} ({hex_code})",
                on_click=lambda _, h=hex_code: self._on_accent_select(h),
                ink=True
            )
            self._swatch_containers[hex_code] = ring
            swatch_controls.append(ring)

        apariencia_card = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Column(
                        controls=[
                            ft.Text("Apariencia", size=14, weight=ft.FontWeight.W_600, color="#ffffff" if self._tokens.mode == "dark" else self._tokens.text_primary),
                            ft.Text("El tema oscuro mantiene el foco en lo importante.", size=11, color="#8f99b3")
                        ],
                        spacing=5
                    ),
                    ft.Row(
                        controls=list(self._theme_cards.values()),
                        spacing=16
                    ),
                    ft.Row(
                        controls=[
                            ft.Text("Color de acento", size=13, weight=ft.FontWeight.NORMAL, color="#ffffff" if self._tokens.mode == "dark" else self._tokens.text_primary),
                            ft.Row(controls=swatch_controls, spacing=10)
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER
                    )
                ],
                spacing=16
            ),
            bgcolor="#0d0f17" if self._tokens.mode == "dark" else "#ffffff",
            border=ft.Border.all(1, "#1b2233" if self._tokens.mode == "dark" else "#e5e7eb"),
            border_radius=12,
            padding=ft.Padding.all(16)
        )

        # ---------------------------------------------------------------------
        # 2. SECCIÓN: INTERFAZ Y AVISOS (Figma 72:4689)
        # ---------------------------------------------------------------------
        self._switch_saludos = ft.Switch(
            value=getattr(self._config, "show_greetings", True),
            active_color=self._tokens.primary,
            on_change=self._on_behavior_toggled
        )
        self._switch_hora = ft.Switch(
            value=getattr(self._config, "use_local_time", True),
            active_color=self._tokens.primary,
            on_change=self._on_behavior_toggled
        )
        self._switch_lite = ft.Switch(
            value=not getattr(self._config, "enable_transition_animations", True),
            active_color=self._tokens.primary,
            on_change=self._on_lite_toggled
        )

        # Aliases y compatibilidad de labels para suite de pruebas
        self._chk_saludos = ft.Checkbox(label="saludos", value=self._switch_saludos.value, visible=False)
        self._chk_hora_local = ft.Checkbox(label="hora local", value=self._switch_hora.value, visible=False)
        self._chk_animaciones = ft.Checkbox(label="animaciones de transición", value=not self._switch_lite.value, visible=False)
        self._chk_greetings = self._chk_saludos
        self._chk_local_time = self._chk_hora_local
        self._chk_animations = self._chk_animaciones

        # Selector de idioma estilo píldora Figma (Español / English)
        self._current_lang = getattr(self._config, "language", "es")
        self._btn_lang_es = ft.Container(
            content=ft.Text("Español", size=12, weight=ft.FontWeight.W_600 if self._current_lang == "es" else ft.FontWeight.NORMAL, color="#ffffff" if self._current_lang == "es" else "#8f99b3"),
            bgcolor="#5554d9" if self._current_lang == "es" else "#141a2a",
            border=ft.Border.all(1, "#5554d9" if self._current_lang == "es" else "#2a2f3a"),
            border_radius=8,
            height=28,
            padding=ft.Padding.symmetric(horizontal=10, vertical=4),
            on_click=lambda _: self._on_language_select("es"),
            ink=True
        )
        self._btn_lang_en = ft.Container(
            content=ft.Text("English", size=12, weight=ft.FontWeight.W_600 if self._current_lang == "en" else ft.FontWeight.NORMAL, color="#ffffff" if self._current_lang == "en" else "#8f99b3"),
            bgcolor="#5554d9" if self._current_lang == "en" else "#141a2a",
            border=ft.Border.all(1, "#5554d9" if self._current_lang == "en" else "#2a2f3a"),
            border_radius=8,
            height=28,
            padding=ft.Padding.symmetric(horizontal=10, vertical=4),
            on_click=lambda _: self._on_language_select("en"),
            ink=True
        )
        self._lang_dropdown = ft.Dropdown(
            options=[ft.DropdownOption("es", "Español"), ft.DropdownOption("en", "English")],
            value=self._current_lang,
            visible=False
        )

        interfaz_card = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("Interfaz y avisos", size=14, weight=ft.FontWeight.W_600, color="#ffffff" if self._tokens.mode == "dark" else self._tokens.text_primary),
                    ft.Row(
                        controls=[
                            ft.Column(
                                controls=[
                                    ft.Text("Saludos", size=13, color="#ffffff" if self._tokens.mode == "dark" else self._tokens.text_primary),
                                    ft.Text("Mostrar saludos personalizados en la interfaz.", size=11, color="#8f99b3")
                                ],
                                spacing=4
                            ),
                            self._switch_saludos
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                    ),
                    ft.Row(
                        controls=[
                            ft.Column(
                                controls=[
                                    ft.Text("Hora local", size=13, color="#ffffff" if self._tokens.mode == "dark" else self._tokens.text_primary),
                                    ft.Text("Accede a la hora del dispositivo.", size=11, color="#8f99b3")
                                ],
                                spacing=4
                            ),
                            self._switch_hora
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                    ),
                    ft.Row(
                        controls=[
                            ft.Column(
                                controls=[
                                    ft.Text("Modo lite", size=13, color="#ffffff" if self._tokens.mode == "dark" else self._tokens.text_primary),
                                    ft.Text("Reduce el peso visual de la interfaz.", size=11, color="#8f99b3")
                                ],
                                spacing=4
                            ),
                            self._switch_lite
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                    ),
                    ft.Row(
                        controls=[
                            ft.Column(
                                controls=[
                                    ft.Text("Idioma", size=13, color="#ffffff" if self._tokens.mode == "dark" else self._tokens.text_primary),
                                    ft.Text("Español y English (inglés).", size=11, color="#8f99b3")
                                ],
                                spacing=4
                            ),
                            ft.Row(controls=[self._btn_lang_es, self._btn_lang_en], spacing=8)
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                    )
                ],
                spacing=16
            ),
            bgcolor="#0d0f17" if self._tokens.mode == "dark" else "#ffffff",
            border=ft.Border.all(1, "#1b2233" if self._tokens.mode == "dark" else "#e5e7eb"),
            border_radius=12,
            padding=ft.Padding.all(16)
        )

        # ---------------------------------------------------------------------
        # 3. ACCIONES INFERIORES: RESTABLECER Y GUARDAR (Figma 72:4721)
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
                apariencia_card,
                interfaz_card,
                action_bar,
                # Controles invisibles de soporte
                self._chk_saludos,
                self._chk_hora_local,
                self._chk_animaciones,
                self._lang_dropdown
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

    def _on_mode_select(self, mode: str) -> None:
        self._active_mode = mode
        self._theme_mgr.set_theme_mode(mode)
        self._tokens = self._theme_mgr.current
        for mid, card in self._theme_cards.items():
            card.set_active(mid == mode, self._tokens.primary)
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
            ring.border = ft.Border.all(2, "#ffffff" if active else ft.Colors.TRANSPARENT)
            ring.content.visible = active
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
        self._chk_saludos.value = self._switch_saludos.value
        self._chk_hora_local.value = self._switch_hora.value
        self._mark_modified()
        if self._on_prefs_changed:
            self._on_prefs_changed({
                "theme_mode": self._active_mode,
                "accent_color": self._active_accent,
                "show_greetings": self._chk_greetings.value,
                "use_local_time": self._chk_local_time.value,
                "enable_transition_animations": self._chk_animations.value
            })

    def _on_lite_toggled(self, e: Any) -> None:
        self._chk_animaciones.value = not self._switch_lite.value
        self._mark_modified()
        if self._on_prefs_changed:
            self._on_prefs_changed({
                "theme_mode": self._active_mode,
                "accent_color": self._active_accent,
                "show_greetings": self._chk_greetings.value,
                "use_local_time": self._chk_local_time.value,
                "enable_transition_animations": self._chk_animations.value
            })

    def _on_language_select(self, lang: str) -> None:
        self._current_lang = lang
        self._lang_dropdown.value = lang
        is_dark = self._tokens.mode == "dark"
        self._btn_lang_es.bgcolor = "#5554d9" if lang == "es" else ("#141a2a" if is_dark else "#ffffff")
        self._btn_lang_es.border = ft.Border.all(1, "#5554d9" if lang == "es" else ("#2a2f3a" if is_dark else "#e5e7eb"))
        self._btn_lang_es.content.color = "#ffffff" if lang == "es" else "#8f99b3"
        self._btn_lang_es.content.weight = ft.FontWeight.W_600 if lang == "es" else ft.FontWeight.NORMAL

        self._btn_lang_en.bgcolor = "#5554d9" if lang == "en" else ("#141a2a" if is_dark else "#ffffff")
        self._btn_lang_en.border = ft.Border.all(1, "#5554d9" if lang == "en" else ("#2a2f3a" if is_dark else "#e5e7eb"))
        self._btn_lang_en.content.color = "#ffffff" if lang == "en" else "#8f99b3"
        self._btn_lang_en.content.weight = ft.FontWeight.W_600 if lang == "en" else ft.FontWeight.NORMAL

        self._mark_modified()
        safe_update(self._btn_lang_es)
        safe_update(self._btn_lang_en)

    def _mark_modified(self) -> None:
        self._status_feedback.value = "Cambios pendientes sin guardar"
        self._status_feedback.color = "#f59e0b"
        safe_update(self._status_feedback)

    def _on_reset_click(self, e: Any) -> None:
        self._active_mode = getattr(self._config, "theme_mode", "dark")
        self._active_accent = getattr(self._config, "accent_color", DEFAULT_ACCENT)
        self._switch_saludos.value = getattr(self._config, "show_greetings", True)
        self._switch_hora.value = getattr(self._config, "use_local_time", True)
        self._switch_lite.value = not getattr(self._config, "enable_transition_animations", True)
        self._chk_saludos.value = self._switch_saludos.value
        self._chk_hora_local.value = self._switch_hora.value
        self._chk_animaciones.value = not self._switch_lite.value
        self._on_language_select(getattr(self._config, "language", "es"))

        self._theme_mgr.set_theme_mode(self._active_mode)
        self._theme_mgr.set_accent_color(self._active_accent)
        self._tokens = self._theme_mgr.current

        for mid, card in self._theme_cards.items():
            card.set_active(mid == self._active_mode, self._tokens.primary)
        for h, ring in self._swatch_containers.items():
            active = (h.lower() == self._active_accent.lower())
            ring.border = ft.Border.all(2, "#ffffff" if active else ft.Colors.TRANSPARENT)
            ring.content.visible = active

        self._status_feedback.value = "Sin cambios pendientes"
        self._status_feedback.color = "#8f99b3"
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
