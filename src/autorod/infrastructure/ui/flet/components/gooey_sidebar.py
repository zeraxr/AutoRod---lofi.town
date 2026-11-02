"""Barra lateral moderna con 6 pestañas, colapso fluido y diseño oficial Figma 1:1."""

import webbrowser
from typing import Callable, Any
import flet as ft
from autorod.infrastructure.ui.flet.theme import ThemeManager, ThemeTokens
from autorod.infrastructure.ui.flet.utils import safe_update, get_asset_path


class FletCollapsibleGooeySidebar(ft.Container):
    """
    Barra lateral inteligente (Side Navigation) estrictamente alineada con Figma:
    - 6 pestañas oficiales: Inicio, Configuración, Personalización, Telemetría, Parámetros, Ayuda.
    - Soporte completo para colapso compacto (72px) y expandido (220px).
    - Indicador visual activo vertical con color de tema reactivo.
    - Botón fijado inferior 'Contacto · Discord' y alternador de colapso.
    - Tematización dual: Modo Oscuro (#1a1b26) y Modo Claro (#dadde9).
    """

    TAB_ITEMS = [
        ("dashboard", ft.Icons.DASHBOARD_ROUNDED, "Inicio"),
        ("settings", ft.Icons.SETTINGS_ROUNDED, "Configuración"),
        ("palette", ft.Icons.PALETTE_ROUNDED, "Personalización"),
        ("telemetry", ft.Icons.SHOW_CHART_ROUNDED, "Telemetría"),
        ("parameters", ft.Icons.TUNE_ROUNDED, "Parámetros"),
        ("help", ft.Icons.HELP_OUTLINE_ROUNDED, "Ayuda"),
    ]

    EXPANDED_WIDTH = 220
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
        self._tab_badges: dict[str, ft.Container] = {}

        # ---------------------------------------------------------------------
        # 1. CABECERA DE LA MARCA (Figma 1:1)
        # ---------------------------------------------------------------------
        self._header_title = ft.Text("AutoRod", size=15, weight=ft.FontWeight.BOLD, color=self._theme.text_primary)
        self._header_badge = ft.Container(
            content=ft.Text("v2.0", size=9, weight=ft.FontWeight.BOLD, color="#ffffff"),
            bgcolor=self._theme.primary,
            border_radius=4,
            padding=ft.Padding.symmetric(horizontal=5, vertical=1)
        )

        svg_logo = get_asset_path("icons/autorod_figma.svg")
        logo_png = get_asset_path("icons/logo_32.png")
        if not logo_png.is_file():
            logo_png = get_asset_path("icons/logo.png")

        logo_content: ft.Control
        if svg_logo.is_file():
            logo_content = ft.Image(src=str(svg_logo), width=22, height=22, fit=ft.BoxFit.CONTAIN)
        else:
            logo_content = ft.Image(src=str(logo_png), width=22, height=22, fit=ft.BoxFit.CONTAIN)

        self._logo_box = ft.Container(
            content=logo_content,
            width=32,
            height=32,
            alignment=ft.Alignment(0, 0),
            border_radius=8,
            bgcolor=self._theme.card_bg,
            border=ft.Border.all(1, self._theme.card_border)
        )

        self._brand_row = ft.Row(
            controls=[
                self._logo_box,
                ft.Row(controls=[self._header_title, self._header_badge], spacing=6)
            ],
            spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.CENTER
        )

        header_layout = ft.Container(
            content=self._brand_row,
            padding=ft.Padding.symmetric(horizontal=8, vertical=6),
            border_radius=8,
            margin=ft.Margin.only(bottom=8)
        )

        # ---------------------------------------------------------------------
        # 2. PESTAÑAS DE NAVEGACIÓN (6 Pestañas Oficiales)
        # ---------------------------------------------------------------------
        tabs_column = ft.Column(spacing=4)
        for idx, (tab_id, icon_data, label) in enumerate(self.TAB_ITEMS):
            is_active = (tab_id == self._active_tab)

            indicator = ft.Container(
                width=3,
                height=18,
                border_radius=2,
                bgcolor=self._theme.primary if is_active else ft.Colors.TRANSPARENT,
                animate=ft.Animation(180, ft.AnimationCurve.EASE_OUT)
            )
            self._tab_indicators[tab_id] = indicator

            icon_ctrl = ft.Icon(
                icon_data,
                size=18,
                color=self._theme.primary if is_active else self._theme.text_secondary
            )
            self._tab_icons[tab_id] = icon_ctrl

            text_ctrl = ft.Text(
                label,
                size=12.5,
                weight=ft.FontWeight.BOLD if is_active else ft.FontWeight.W_500,
                color=self._theme.text_primary if is_active else self._theme.text_secondary
            )
            self._tab_texts[tab_id] = text_ctrl

            shortcut_badge = ft.Container(
                content=ft.Text(str(idx + 1), size=9, weight=ft.FontWeight.BOLD, color=self._theme.text_muted),
                bgcolor=self._theme.sub_bg,
                border=ft.Border.all(1, self._theme.card_border),
                border_radius=4,
                padding=ft.Padding.symmetric(horizontal=5, vertical=1)
            )
            self._tab_badges[tab_id] = shortcut_badge

            tab_row = ft.Row(
                controls=[
                    indicator,
                    ft.Container(content=icon_ctrl, width=24, alignment=ft.Alignment(0, 0)),
                    text_ctrl,
                    ft.Container(expand=True),
                    shortcut_badge
                ],
                spacing=6,
                vertical_alignment=ft.CrossAxisAlignment.CENTER
            )

            pill = ft.Container(
                content=tab_row,
                height=38,
                padding=ft.Padding.only(left=2, right=8),
                border_radius=8,
                bgcolor=self._theme.card_bg if is_active else ft.Colors.TRANSPARENT,
                border=ft.Border.all(1, self._theme.card_border) if is_active else None,
                animate=ft.Animation(180, ft.AnimationCurve.EASE_OUT),
                on_click=lambda e, tid=tab_id: self.select_tab(tid),
                on_hover=lambda e, tid=tab_id: self._on_tab_hover(e, tid),
                tooltip=label,
                ink=True
            )
            self._tab_containers[tab_id] = pill
            tabs_column.controls.append(pill)

        # ---------------------------------------------------------------------
        # 3. FOOTER: BOTÓN DISCORD Y ALTERNADOR DE COLAPSO (Figma 1:1)
        # ---------------------------------------------------------------------
        discord_svg = get_asset_path("icons/discord.svg")
        discord_icon_ctrl: ft.Control
        if discord_svg.is_file():
            discord_icon_ctrl = ft.Image(src=str(discord_svg), width=13, height=13, fit=ft.BoxFit.CONTAIN)
        else:
            discord_icon_ctrl = ft.Icon(ft.Icons.FORUM_ROUNDED, size=14, color="#ffffff")

        self._discord_icon_box = ft.Container(
            content=discord_icon_ctrl,
            width=20,
            height=20,
            border_radius=5,
            bgcolor="#5865f2",
            alignment=ft.Alignment(0, 0)
        )
        self._discord_text = ft.Text(
            "Contacto · Discord",
            size=11.5,
            weight=ft.FontWeight.W_500,
            color=self._theme.text_primary
        )
        self._discord_btn = ft.Container(
            content=ft.Row(
                controls=[
                    self._discord_icon_box,
                    self._discord_text
                ],
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER
            ),
            height=36,
            padding=ft.Padding.symmetric(horizontal=10),
            border_radius=8,
            bgcolor=self._theme.card_bg,
            border=ft.Border.all(1, self._theme.card_border),
            on_click=lambda _: self._open_discord_link(),
            tooltip="Comunidad y Soporte Oficial en Discord",
            ink=True
        )

        self._collapse_icon = ft.Icon(ft.Icons.KEYBOARD_DOUBLE_ARROW_LEFT_ROUNDED, size=16, color=self._theme.text_secondary)
        self._collapse_text = ft.Text("Colapsar", size=11, color=self._theme.text_secondary)
        self._collapse_btn = ft.Container(
            content=ft.Row(
                controls=[
                    self._collapse_icon,
                    self._collapse_text
                ],
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER
            ),
            height=32,
            padding=ft.Padding.symmetric(horizontal=10),
            border_radius=6,
            on_click=lambda _: self.toggle_collapsed(),
            tooltip="Alternar barra lateral compacta / expandida",
            ink=True
        )

        super().__init__(
            content=ft.Column(
                controls=[
                    header_layout,
                    tabs_column,
                    ft.Container(expand=True),
                    self._discord_btn,
                    self._collapse_btn
                ],
                spacing=6,
                expand=True
            ),
            width=self.EXPANDED_WIDTH,
            bgcolor=self._theme.shell_bg,
            border=None,
            padding=ft.Padding.all(8),
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
            pill.bgcolor = self._theme.sub_bg
            pill.border = ft.Border.all(1, self._theme.card_border)
        else:
            pill.bgcolor = ft.Colors.TRANSPARENT
            pill.border = None
        safe_update(pill)

    def _on_theme_updated(self, tokens: ThemeTokens) -> None:
        self._theme = tokens
        self.bgcolor = tokens.shell_bg
        self._header_title.color = tokens.text_primary
        self._header_badge.bgcolor = tokens.primary
        self._logo_box.bgcolor = tokens.card_bg
        self._logo_box.border = ft.Border.all(1, tokens.card_border)
        self._discord_btn.bgcolor = tokens.card_bg
        self._discord_btn.border = ft.Border.all(1, tokens.card_border)
        self._discord_text.color = tokens.text_primary
        self._collapse_icon.color = tokens.text_secondary
        self._collapse_text.color = tokens.text_secondary
        self._render_tabs_state()
        safe_update(self)

    def toggle_collapsed(self) -> None:
        self._is_collapsed = not self._is_collapsed
        self.width = self.COLLAPSED_WIDTH if self._is_collapsed else self.EXPANDED_WIDTH
        self._collapse_icon.name = ft.Icons.KEYBOARD_DOUBLE_ARROW_RIGHT_ROUNDED if self._is_collapsed else ft.Icons.KEYBOARD_DOUBLE_ARROW_LEFT_ROUNDED
        self._collapse_text.visible = not self._is_collapsed

        for tid, text_ctrl in self._tab_texts.items():
            text_ctrl.visible = not self._is_collapsed

        for tid, badge in self._tab_badges.items():
            badge.visible = not self._is_collapsed

        self._header_title.visible = not self._is_collapsed
        self._header_badge.visible = not self._is_collapsed
        self._discord_text.visible = not self._is_collapsed

        safe_update(self)

    def select_tab(self, tab_id: str) -> None:
        self._active_tab = tab_id
        self._render_tabs_state()
        safe_update(self)
        self._on_tab_selected(tab_id)

    def _render_tabs_state(self) -> None:
        for tid, pill in self._tab_containers.items():
            is_active = (tid == self._active_tab)

            pill.bgcolor = self._theme.card_bg if is_active else ft.Colors.TRANSPARENT
            pill.border = ft.Border.all(1, self._theme.card_border) if is_active else None

            indicator = self._tab_indicators.get(tid)
            if indicator:
                indicator.bgcolor = self._theme.primary if is_active else ft.Colors.TRANSPARENT

            text_ctrl = self._tab_texts[tid]
            text_ctrl.color = self._theme.text_primary if is_active else self._theme.text_secondary
            text_ctrl.weight = ft.FontWeight.BOLD if is_active else ft.FontWeight.W_500

            icon_ctrl = self._tab_icons[tid]
            if isinstance(icon_ctrl, ft.Icon):
                icon_ctrl.color = self._theme.primary if is_active else self._theme.text_secondary
