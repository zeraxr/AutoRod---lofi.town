"""Barra lateral moderna con 6 pestañas y diseño oficial Figma 1:1."""

import webbrowser
from typing import Callable, Any
import flet as ft
from autorod.infrastructure.ui.flet.theme import ThemeManager, ThemeTokens
from autorod.infrastructure.ui.flet.utils import safe_update, get_asset_path


class FletCollapsibleGooeySidebar(ft.Container):
    """
    Barra lateral de navegación oficial Figma 1:1:
    - 5 pestañas activas: Inicio, Configuración, Personalización, Telemetría, Ayuda.
    - Pestaña 'Parámetros' deprecada y deshabilitada para blindar las constantes del motor de visión.
    - Pestaña activa con estilo píldora sobrio (#141a2a / #2a2f3a) y texto blanco.
    - Sin badges numéricos ni duplicidad de logotipo (el logotipo está en la barra superior).
    - Botón inferior fijado 'Contacto' con icono oficial de Discord.
    """

    TAB_ITEMS = [
        ("dashboard", ft.Icons.HOME_ROUNDED, "Inicio"),
        ("settings", ft.Icons.SETTINGS_ROUNDED, "Configuración"),
        ("palette", ft.Icons.PALETTE_ROUNDED, "Personalización"),
        ("telemetry", ft.Icons.SHOW_CHART_ROUNDED, "Telemetría"),
        ("help", ft.Icons.HELP_OUTLINE_ROUNDED, "Ayuda"),
    ]

    EXPANDED_WIDTH = 236
    COLLAPSED_WIDTH = 72

    def __init__(
        self,
        on_tab_selected: Callable[[str], None],
        theme_manager: ThemeManager | None = None,
        settings_view: ft.Control | None = None
    ) -> None:
        self._on_tab_selected = on_tab_selected
        self._theme_mgr = theme_manager or ThemeManager.get_instance()
        self._theme: ThemeTokens = self._theme_mgr.current
        self._settings_view = settings_view

        self._is_collapsed = False
        self._active_tab = "dashboard"

        self._tab_containers: dict[str, ft.Container] = {}
        self._tab_texts: dict[str, ft.Text] = {}
        self._tab_icons: dict[str, ft.Control] = {}
        self._tab_indicators: dict[str, ft.Container] = {}

        # ---------------------------------------------------------------------
        # 1. PESTAÑAS DE NAVEGACIÓN (Figma 1:1: Solo Icono + Texto)
        # ---------------------------------------------------------------------
        tabs_column = ft.Column(spacing=5)
        for idx, (tab_id, icon_data, label) in enumerate(self.TAB_ITEMS):
            is_active = (tab_id == self._active_tab)

            icon_ctrl = ft.Icon(
                icon_data,
                size=18,
                color="#ffffff" if is_active else self._theme.text_muted
            )
            self._tab_icons[tab_id] = icon_ctrl

            text_ctrl = ft.Text(
                label,
                size=13,
                weight=ft.FontWeight.W_600 if is_active else ft.FontWeight.NORMAL,
                color="#ffffff" if is_active else self._theme.text_muted
            )
            self._tab_texts[tab_id] = text_ctrl

            tab_row = ft.Row(
                controls=[
                    ft.Container(content=icon_ctrl, width=20, alignment=ft.Alignment(0, 0)),
                    text_ctrl
                ],
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER
            )

            active_bg = "#0f141d" if self._theme.mode == "dark" else "#f2f3f8"
            pill = ft.Container(
                content=tab_row,
                height=42,
                padding=ft.Padding.symmetric(horizontal=12),
                border_radius=8,
                bgcolor=active_bg if is_active else ft.Colors.TRANSPARENT,
                border=None,
                animate=ft.Animation(160, ft.AnimationCurve.EASE_OUT),
                on_click=lambda e, tid=tab_id: self.select_tab(tid),
                on_hover=lambda e, tid=tab_id: self._on_tab_hover(e, tid),
                tooltip=label,
                ink=True
            )
            self._tab_containers[tab_id] = pill
            tabs_column.controls.append(pill)

        # ---------------------------------------------------------------------
        # 2. FOOTER: BOTÓN DISCORD 'Contacto' (Figma 1:1)
        # ---------------------------------------------------------------------
        discord_svg = get_asset_path("icons/discord.svg")
        discord_icon_ctrl: ft.Control
        if discord_svg.is_file():
            discord_icon_ctrl = ft.Image(src=str(discord_svg), width=14, height=14, fit=ft.BoxFit.CONTAIN)
        else:
            discord_icon_ctrl = ft.Icon(ft.Icons.FORUM_ROUNDED, size=14, color="#ffffff")

        self._discord_icon_box = ft.Container(
            content=discord_icon_ctrl,
            width=18,
            height=18,
            border_radius=5,
            bgcolor="#5865f2",
            alignment=ft.Alignment(0, 0)
        )
        self._discord_text = ft.Text(
            "Contacto",
            size=13,
            weight=ft.FontWeight.W_600,
            color="#ffffff" if self._theme.mode == "dark" else self._theme.text_primary
        )
        contact_bg = "#0f141d" if self._theme.mode == "dark" else "#f2f3f8"
        contact_border = "#2a2f3a" if self._theme.mode == "dark" else "#e5e7eb"
        self._discord_btn = ft.Container(
            content=ft.Row(
                controls=[
                    self._discord_icon_box,
                    self._discord_text
                ],
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER
            ),
            height=42,
            padding=ft.Padding.symmetric(horizontal=12),
            border_radius=8,
            bgcolor=contact_bg,
            border=ft.Border.all(1, contact_border),
            on_click=lambda _: self._open_discord_link(),
            tooltip="Comunidad y Soporte Oficial en Discord",
            ink=True
        )

        super().__init__(
            content=ft.Column(
                controls=[
                    tabs_column,
                    ft.Container(expand=True),
                    self._discord_btn
                ],
                spacing=5,
                expand=True
            ),
            width=self.EXPANDED_WIDTH,
            bgcolor=self._theme.shell_bg,
            border=None,
            padding=ft.Padding.only(left=16, right=16, top=20, bottom=20),
            animate=ft.Animation(220, ft.AnimationCurve.FAST_OUT_SLOWIN)
        )

        self._theme_mgr.subscribe(self._on_theme_updated)

    def _open_discord_link(self) -> None:
        try:
            webbrowser.open("https://discord.gg/autorod")
        except Exception:
            pass

    def _on_tab_hover(self, e: ft.HoverEvent, tab_id: str) -> None:
        if tab_id == self._active_tab:
            return
        pill = self._tab_containers.get(tab_id)
        if not pill:
            return
        if e.data == "true":
            pill.bgcolor = "#161c2e" if self._theme.mode == "dark" else "#e5e7eb"
            pill.border = ft.Border.all(1, "#2a2f3a" if self._theme.mode == "dark" else "#d1d5db")
        else:
            pill.bgcolor = ft.Colors.TRANSPARENT
            pill.border = None
        safe_update(pill)

    def _on_theme_updated(self, tokens: ThemeTokens) -> None:
        self._theme = tokens
        self.bgcolor = tokens.shell_bg
        contact_bg = "#0f141d" if tokens.mode == "dark" else "#f2f3f8"
        contact_border = "#2a2f3a" if tokens.mode == "dark" else "#e5e7eb"
        self._discord_btn.bgcolor = contact_bg
        self._discord_btn.border = ft.Border.all(1, contact_border)
        self._discord_text.color = "#ffffff" if tokens.mode == "dark" else tokens.text_primary
        self._render_tabs_state()
        safe_update(self)

    def toggle_collapsed(self) -> None:
        self._is_collapsed = not self._is_collapsed
        self.width = self.COLLAPSED_WIDTH if self._is_collapsed else self.EXPANDED_WIDTH

        for tid, text_ctrl in self._tab_texts.items():
            text_ctrl.visible = not self._is_collapsed

        self._discord_text.visible = not self._is_collapsed
        safe_update(self)

    def select_tab(self, tab_id: str) -> None:
        self._active_tab = tab_id
        self._render_tabs_state()
        safe_update(self)
        self._on_tab_selected(tab_id)

    def _render_tabs_state(self) -> None:
        active_bg = "#0f141d" if self._theme.mode == "dark" else "#f2f3f8"
        active_color = "#ffffff" if self._theme.mode == "dark" else self._theme.text_primary
        inactive_color = self._theme.text_muted

        for tid, pill in self._tab_containers.items():
            is_active = (tid == self._active_tab)

            pill.bgcolor = active_bg if is_active else ft.Colors.TRANSPARENT
            pill.border = None

            text_ctrl = self._tab_texts[tid]
            text_ctrl.color = active_color if is_active else inactive_color
            text_ctrl.weight = ft.FontWeight.W_600 if is_active else ft.FontWeight.NORMAL

            icon_ctrl = self._tab_icons[tid]
            if isinstance(icon_ctrl, ft.Icon):
                icon_ctrl.color = active_color if is_active else inactive_color
