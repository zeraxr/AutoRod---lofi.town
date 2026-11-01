"""Barra lateral colapsable moderna con navegación fluida y diseño sobrio en Flet."""

from typing import Callable, Any
import flet as ft
from autorod.infrastructure.ui.flet.theme import ThemeManager, ThemeTokens
from autorod.infrastructure.ui.flet.utils import safe_update, get_asset_path


class FletCollapsibleGooeySidebar(ft.Container):
    """
    Barra lateral inteligente (Side Navigation) con estética moderna minimalista tipo Linear/Raycast.
    - Soporte completo para colapso compacto (72px), expandido (220px) y panel de parámetros (320px).
    - Integración directa del apartado de configuración de parámetros dentro de la propia barra lateral.
    - Indicador líquido activo vertical con color de tema reactivo.
    - Atajos visuales de teclado ([1], [2], [3], [4]).
    - Micro-interacciones de hover y clics táctiles con curvas de animación fluidas.
    """

    TAB_ITEMS = [
        ("dashboard", ft.Icons.DASHBOARD_ROUNDED, "Dashboard"),
        ("settings", ft.Icons.TUNE_ROUNDED, "Configuración"),
        ("palette", ft.Icons.PALETTE_ROUNDED, "Personalización"),
        ("telemetry", ft.Icons.QUERY_STATS_ROUNDED, "Telemetría"),
    ]

    SETTINGS_WIDTH = 320
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
        self._is_settings_open = False
        self._active_tab = "dashboard"

        self._tab_containers: dict[str, ft.Container] = {}
        self._tab_texts: dict[str, ft.Text] = {}
        self._tab_icons: dict[str, ft.Control] = {}
        self._tab_indicators: dict[str, ft.Container] = {}
        self._tab_badges: dict[str, ft.Container] = {}

        # 1. Cabecera de la Marca
        self._header_title = ft.Text("AutoRod", size=14, weight=ft.FontWeight.BOLD, color="#f8fafc")
        self._header_tag = ft.Text("VISUAL AUTOMATION", size=9, weight=ft.FontWeight.W_600, color=self._theme.primary)
        self._chevron_icon = ft.Icon(ft.Icons.CHEVRON_LEFT_ROUNDED, size=16, color="#64748b")
        self._header_status_dot = ft.Container(
            width=7,
            height=7,
            border_radius=4,
            bgcolor="#10b981",
            shadow=None
        )

        logo_path = get_asset_path("icons/logo_32.png")
        if not logo_path.is_file():
            logo_path = get_asset_path("icons/logo.png")

        logo_content: ft.Control = ft.Image(
            src=str(logo_path),
            width=22,
            height=22,
            fit=ft.BoxFit.CONTAIN
        )

        logo_box = ft.Container(
            content=logo_content,
            width=36,
            height=36,
            alignment=ft.Alignment(0, 0),
            border_radius=8,
            bgcolor="#111217",
            border=ft.Border.all(1, "#1c1d24")
        )

        header_layout = ft.Container(
            content=ft.Row(
                controls=[
                    logo_box,
                    ft.Column(
                        controls=[
                            ft.Row(controls=[self._header_title, self._header_status_dot], spacing=5),
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
            border_radius=8,
            ink=True,
            tooltip="Alternar barra lateral compacta"
        )

        # 2. Contenedor del apartado de Parámetros integrado en el Sidebar
        self._settings_container: ft.Container | None = None
        if self._settings_view is not None:
            self._settings_container = ft.Container(
                content=self._settings_view,
                visible=False,
                padding=ft.Padding.only(left=2, right=2, top=4, bottom=6)
            )

        # 3. Pestañas de Navegación
        tabs_column = ft.Column(spacing=4)
        for idx, (tab_id, icon_data, label) in enumerate(self.TAB_ITEMS):
            is_active = (tab_id == self._active_tab)

            indicator = ft.Container(
                width=3,
                height=20,
                border_radius=2,
                bgcolor=self._theme.primary if is_active else ft.Colors.TRANSPARENT,
                animate=ft.Animation(200, ft.AnimationCurve.EASE_OUT_CUBIC)
            )
            self._tab_indicators[tab_id] = indicator

            if isinstance(icon_data, str):
                icon_ctrl: ft.Control = ft.Text(icon_data, size=16)
            else:
                icon_ctrl = ft.Icon(
                    icon_data,
                    size=17,
                    color=self._theme.primary if is_active else "#94a3b8"
                )
            self._tab_icons[tab_id] = icon_ctrl

            text_ctrl = ft.Text(
                label,
                size=12,
                weight=ft.FontWeight.BOLD if is_active else ft.FontWeight.W_500,
                color="#ffffff" if is_active else "#9ca3af"
            )
            self._tab_texts[tab_id] = text_ctrl

            shortcut_badge = ft.Container(
                content=ft.Text(str(idx + 1), size=9, weight=ft.FontWeight.BOLD, color="#71717a"),
                bgcolor="#141417",
                border=ft.Border.all(1, "#222226"),
                border_radius=4,
                padding=ft.Padding.symmetric(horizontal=6, vertical=2)
            )
            self._tab_badges[tab_id] = shortcut_badge

            tab_row = ft.Row(
                controls=[
                    indicator,
                    ft.Container(content=icon_ctrl, width=28, alignment=ft.Alignment(0, 0)),
                    text_ctrl,
                    ft.Container(expand=True),
                    shortcut_badge
                ],
                spacing=6,
                vertical_alignment=ft.CrossAxisAlignment.CENTER
            )

            pill = ft.Container(
                content=tab_row,
                height=42,
                padding=ft.Padding.only(left=2, right=10),
                border_radius=8,
                bgcolor=self._theme.accent_subtle if is_active else ft.Colors.TRANSPARENT,
                border=ft.Border.all(1, self._theme.border_active) if is_active else None,
                animate=ft.Animation(220, ft.AnimationCurve.EASE_OUT_CUBIC),
                on_click=lambda e, tid=tab_id: self._on_tab_click(tid),
                on_hover=lambda e, tid=tab_id: self._on_tab_hover(e, tid),
                tooltip=label,
                ink=True
            )
            self._tab_containers[tab_id] = pill
            tabs_column.controls.append(pill)

            # Insertar el panel de parámetros directamente debajo de la pestaña Configuración
            if tab_id == "settings" and self._settings_container is not None:
                tabs_column.controls.append(self._settings_container)

        super().__init__(
            content=ft.Column(
                controls=[
                    header_layout,
                    tabs_column
                ],
                spacing=8,
                expand=True,
                scroll=ft.ScrollMode.ADAPTIVE
            ),
            width=self.EXPANDED_WIDTH,
            bgcolor="#070709",
            border=None,
            padding=ft.Padding.all(8),
            animate=ft.Animation(260, ft.AnimationCurve.FAST_OUT_SLOWIN)
        )

        self._theme_mgr.subscribe(self._on_theme_updated)

    def _on_tab_click(self, tid: str) -> None:
        """Maneja el clic interactivo en la pestaña del Sidebar (permite alternar apertura de parámetros)."""
        if tid == "settings" and self._active_tab == "settings" and self._is_settings_open:
            self.select_tab("dashboard")
            return
        self.select_tab(tid)

    def _on_tab_hover(self, e: ft.HoverEvent, tab_id: str) -> None:
        """Efecto hover suave y reactivo para pestañas no activas."""
        if tab_id == self._active_tab:
            return
        pill = self._tab_containers.get(tab_id)
        if not pill:
            return
        if e.data == "true":
            pill.bgcolor = "#18181b"
            pill.border = ft.Border.all(1, "#27272a")
        else:
            pill.bgcolor = ft.Colors.TRANSPARENT
            pill.border = None
        safe_update(pill)

    def _on_theme_updated(self, tokens: ThemeTokens) -> None:
        self._theme = tokens
        self._header_tag.color = tokens.primary
        self._render_tabs_state()
        safe_update(self)

    def toggle_collapsed(self) -> None:
        self._is_collapsed = not self._is_collapsed
        if self._is_collapsed:
            self.width = self.COLLAPSED_WIDTH
            if self._settings_container:
                self._settings_container.visible = False
        else:
            if self._active_tab == "settings" and self._settings_container:
                self.width = self.SETTINGS_WIDTH
                self._settings_container.visible = True
            else:
                self.width = self.EXPANDED_WIDTH
                if self._settings_container:
                    self._settings_container.visible = False

        self._chevron_icon.name = ft.Icons.CHEVRON_RIGHT_ROUNDED if self._is_collapsed else ft.Icons.CHEVRON_LEFT_ROUNDED

        for tid, text_ctrl in self._tab_texts.items():
            text_ctrl.visible = not self._is_collapsed

        for tid, badge in self._tab_badges.items():
            badge.visible = not self._is_collapsed

        self._header_title.visible = not self._is_collapsed
        self._header_tag.visible = not self._is_collapsed
        self._chevron_icon.visible = not self._is_collapsed

        safe_update(self)

    def select_tab(self, tab_id: str) -> None:
        self._active_tab = tab_id
        if tab_id == "settings" and self._settings_container is not None:
            self._is_settings_open = True
            self._settings_container.visible = True
            if not self._is_collapsed:
                self.width = self.SETTINGS_WIDTH
        else:
            self._is_settings_open = False
            if self._settings_container is not None:
                self._settings_container.visible = False
            if not self._is_collapsed:
                self.width = self.EXPANDED_WIDTH

        self._render_tabs_state()
        safe_update(self)
        self._on_tab_selected(tab_id)

    def _render_tabs_state(self) -> None:
        for tid, pill in self._tab_containers.items():
            is_active = (tid == self._active_tab)

            pill.bgcolor = self._theme.accent_subtle if is_active else ft.Colors.TRANSPARENT
            pill.border = ft.Border.all(1, self._theme.border_active) if is_active else None

            indicator = self._tab_indicators.get(tid)
            if indicator:
                indicator.bgcolor = self._theme.primary if is_active else ft.Colors.TRANSPARENT

            text_ctrl = self._tab_texts[tid]
            text_ctrl.color = "#ffffff" if is_active else "#9ca3af"
            text_ctrl.weight = ft.FontWeight.BOLD if is_active else ft.FontWeight.W_500

            icon_ctrl = self._tab_icons[tid]
            if isinstance(icon_ctrl, ft.Icon):
                icon_ctrl.color = self._theme.primary if is_active else "#94a3b8"
            elif isinstance(icon_ctrl, ft.Text):
                icon_ctrl.color = self._theme.primary if is_active else "#9ca3af"
