"""Barra lateral colapsable con navegación fluida y animaciones en Flet."""

from typing import Callable, Any
import flet as ft
from autorod.infrastructure.ui.flet.theme import ThemeManager, ThemeTokens
from autorod.infrastructure.ui.flet.utils import safe_update


class FletCollapsibleGooeySidebar(ft.Container):
    """Barra lateral inteligente con colapso de acordeón y selector de pestañas en Flet."""

    TAB_ITEMS = [
        ("dashboard", "🖥️", "Visor / Dashboard"),
        ("settings", "⚙️", "Configuración"),
        ("palette", "🎨", "Personalizar Colores"),
        ("telemetry", "📊", "Telemetría / Logs"),
    ]

    EXPANDED_WIDTH = 220
    COLLAPSED_WIDTH = 72

    def __init__(
        self,
        on_tab_selected: Callable[[str], None],
        theme_manager: ThemeManager | None = None
    ) -> None:
        self._on_tab_selected = on_tab_selected
        self._theme_mgr = theme_manager or ThemeManager.get_instance()
        self._theme: ThemeTokens = self._theme_mgr.current

        self._is_collapsed = False
        self._active_tab = "dashboard"

        self._tab_containers: dict[str, ft.Container] = {}
        self._tab_texts: dict[str, ft.Text] = {}
        self._tab_icons: dict[str, ft.Text] = {}

        self._header_title = ft.Text("AutoRod", size=15, weight=ft.FontWeight.BOLD, color="#ffffff")
        self._header_tag = ft.Text("Visual Automation", size=10, weight=ft.FontWeight.W_500, color="#94a3b8")
        self._chevron_icon = ft.Text("◀", size=11, color="#64748b")
        self._status_dot = ft.Container(
            width=8,
            height=8,
            border_radius=4,
            bgcolor="#3ecf8e",
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=6, color="#3ecf8e")
        )

        header_layout = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Container(
                        content=ft.Text("🎣", size=20),
                        width=42,
                        height=42,
                        alignment=ft.Alignment(0, 0),
                        border_radius=10,
                        bgcolor="#161822",
                        border=ft.Border.all(1, "#232738")
                    ),
                    ft.Column(
                        controls=[
                            ft.Row(controls=[self._header_title, self._status_dot], spacing=6),
                            self._header_tag
                        ],
                        spacing=1,
                        alignment=ft.MainAxisAlignment.CENTER
                    ),
                    self._chevron_icon
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER
            ),
            padding=ft.Padding.symmetric(horizontal=10, vertical=8),
            on_click=lambda e: self.toggle_collapsed(),
            border_radius=10,
            ink=True
        )

        tabs_column = ft.Column(spacing=6)
        for tab_id, icon, label in self.TAB_ITEMS:
            icon_ctrl = ft.Text(icon, size=16)
            text_ctrl = ft.Text(
                label,
                size=12,
                weight=ft.FontWeight.W_500,
                color="#ffffff" if tab_id == self._active_tab else "#9ca3af"
            )
            self._tab_icons[tab_id] = icon_ctrl
            self._tab_texts[tab_id] = text_ctrl

            tab_row = ft.Row(
                controls=[
                    ft.Container(content=icon_ctrl, width=28, alignment=ft.Alignment(0, 0)),
                    text_ctrl
                ],
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER
            )

            is_active = (tab_id == self._active_tab)
            pill = ft.Container(
                content=tab_row,
                height=42,
                padding=ft.Padding.symmetric(horizontal=10),
                border_radius=10,
                bgcolor=self._theme.accent_subtle if is_active else ft.Colors.TRANSPARENT,
                border=ft.Border.all(1, self._theme.border_active) if is_active else None,
                animate=ft.Animation(220, ft.AnimationCurve.EASE_OUT),
                on_click=lambda e, tid=tab_id: self.select_tab(tid),
                ink=True
            )
            self._tab_containers[tab_id] = pill
            tabs_column.controls.append(pill)

        sep = ft.Container(height=1, bgcolor="#1c1f2b", margin=ft.Margin.symmetric(vertical=6, horizontal=6))

        super().__init__(
            content=ft.Column(
                controls=[
                    header_layout,
                    sep,
                    tabs_column
                ],
                spacing=0
            ),
            width=self.EXPANDED_WIDTH,
            bgcolor="#0d0e15",
            border=ft.Border.only(right=ft.BorderSide(1, "#181a24")),
            padding=ft.Padding.all(8),
            animate=ft.Animation(280, ft.AnimationCurve.FAST_OUT_SLOWIN)
        )

        self._theme_mgr.subscribe(self._on_theme_updated)

    def _on_theme_updated(self, tokens: ThemeTokens) -> None:
        self._theme = tokens
        self._header_tag.color = tokens.primary
        self._render_tabs_state()
        safe_update(self)

    def toggle_collapsed(self) -> None:
        self._is_collapsed = not self._is_collapsed
        self.width = self.COLLAPSED_WIDTH if self._is_collapsed else self.EXPANDED_WIDTH
        self._chevron_icon.value = "▶" if self._is_collapsed else "◀"

        for tid, text_ctrl in self._tab_texts.items():
            text_ctrl.visible = not self._is_collapsed

        self._header_title.visible = not self._is_collapsed
        self._header_tag.visible = not self._is_collapsed
        self._status_dot.visible = not self._is_collapsed
        self._chevron_icon.visible = not self._is_collapsed

        safe_update(self)

    def select_tab(self, tab_id: str) -> None:
        self._active_tab = tab_id
        self._render_tabs_state()
        safe_update(self)
        self._on_tab_selected(tab_id)

    def _render_tabs_state(self) -> None:
        for tid, pill in self._tab_containers.items():
            is_active = (tid == self._active_tab)
            pill.bgcolor = self._theme.accent_subtle if is_active else ft.Colors.TRANSPARENT
            pill.border = ft.Border.all(1, self._theme.border_active) if is_active else None
            text_ctrl = self._tab_texts[tid]
            text_ctrl.color = "#ffffff" if is_active else "#9ca3af"
            text_ctrl.weight = ft.FontWeight.BOLD if is_active else ft.FontWeight.W_500
            icon_ctrl = self._tab_icons[tid]
            icon_ctrl.color = self._theme.primary if is_active else "#9ca3af"
