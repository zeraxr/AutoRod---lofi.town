"""Componentes de botones cinéticos sobrios y de alta precisión para AutoRod en Flet."""

from typing import Callable, Any
import flet as ft
from autorod.infrastructure.ui.flet.theme import ThemeManager, ThemeTokens
from autorod.infrastructure.ui.flet.utils import safe_update, get_control_page


class FletKineticGlowButton(ft.Container):
    """
    Botón interactivo de diseño sobrio, plano y mate (estilo Linear/Raycast).
    - Sin efectos de glow difuso ni sombras artificiales.
    - Soporte completo para glifos vectoriales (ft.Icon) en lugar de emojis.
    - Micro-interacciones de hover con contraste nítido y pulsación táctil (scale=0.98).
    - Confirmación visual de acción con ciclo de reseteo automático.
    """

    def __init__(
        self,
        text: str,
        on_click: Callable[[], None] | None = None,
        width: int = 136,
        height: int = 38,
        is_primary: bool = True,
        confirmed_text: str = "EJECUTADO",
        theme_manager: ThemeManager | None = None,
        tooltip: str | None = None,
        icon: Any | None = None
    ) -> None:
        self._initial_text = text
        self._confirmed_text = confirmed_text
        self._on_click_cmd = on_click
        self._is_primary = is_primary
        self._theme_mgr = theme_manager or ThemeManager.get_instance()
        self._theme: ThemeTokens = self._theme_mgr.current
        self._initial_icon = icon
        self._current_icon = icon

        self._is_hovered = False
        self._is_confirmed = False

        self._btn_text = ft.Text(
            value=self._initial_text,
            size=12,
            weight=ft.FontWeight.W_600,
            color=self._theme.text_on_primary if is_primary else "#e4e4e7",
            text_align=ft.TextAlign.CENTER
        )

        self._icon_ctrl: ft.Icon | None = None
        if self._initial_icon is not None:
            self._icon_ctrl = ft.Icon(
                self._initial_icon,
                size=14,
                color=self._theme.text_on_primary if is_primary else "#a1a1aa"
            )

        if self._icon_ctrl:
            content_layout = ft.Row(
                controls=[self._icon_ctrl, self._btn_text],
                spacing=6,
                alignment=ft.MainAxisAlignment.CENTER,
                vertical_alignment=ft.CrossAxisAlignment.CENTER
            )
        else:
            content_layout = self._btn_text

        super().__init__(
            content=content_layout,
            width=width,
            height=height,
            alignment=ft.Alignment(0, 0),
            border_radius=8,
            animate=ft.Animation(160, ft.AnimationCurve.EASE_OUT),
            animate_scale=ft.Animation(120, ft.AnimationCurve.EASE_OUT),
            on_click=self._handle_click,
            on_hover=self._handle_hover,
            ink=True,
            scale=1.0,
            tooltip=tooltip,
            shadow=None
        )

        self._theme_mgr.subscribe(self._on_theme_updated)
        self._apply_style()

    def _on_theme_updated(self, tokens: ThemeTokens) -> None:
        self._theme = tokens
        self._apply_style()
        safe_update(self)

    def _apply_style(self) -> None:
        primary = self._theme.primary
        hover = self._theme.primary_hover
        text_col = self._theme.text_on_primary

        self.shadow = None

        if self._is_primary:
            if self._is_confirmed:
                self.bgcolor = primary
                self._btn_text.value = self._confirmed_text
                self._btn_text.color = text_col
                self.border = ft.Border.all(1.2, "#ffffff")
                if self._icon_ctrl:
                    self._icon_ctrl.color = text_col
            elif self._is_hovered:
                self.bgcolor = hover
                self._btn_text.value = self._initial_text
                self._btn_text.color = text_col
                self.border = ft.Border.all(1, hover)
                if self._icon_ctrl:
                    self._icon_ctrl.color = text_col
            else:
                self.bgcolor = primary
                self._btn_text.value = self._initial_text
                self._btn_text.color = text_col
                self.border = ft.Border.all(1, hover)
                if self._icon_ctrl:
                    self._icon_ctrl.color = text_col
        else:
            if self._is_hovered:
                self.bgcolor = "#1a1a1e"
                self._btn_text.color = "#ffffff"
                self.border = ft.Border.all(1, "#3f3f46")
                if self._icon_ctrl:
                    self._icon_ctrl.color = "#ffffff"
            else:
                self.bgcolor = "#121214"
                self._btn_text.color = "#e4e4e7"
                self.border = ft.Border.all(1, "#27272a")
                if self._icon_ctrl:
                    self._icon_ctrl.color = "#a1a1aa"

    def set_text(self, text: str, icon: Any | None = None) -> None:
        self._initial_text = text
        if icon is not None and self._icon_ctrl:
            self._icon_ctrl.name = icon
        if not self._is_confirmed:
            self._btn_text.value = text
            safe_update(self)

    def _handle_hover(self, e: ft.HoverEvent) -> None:
        self._is_hovered = (e.data == "true")
        self.scale = 1.02 if self._is_hovered else 1.0
        self._apply_style()
        safe_update(self)

    def _handle_click(self, e: Any) -> None:
        self._is_confirmed = True
        self.scale = 0.98
        self._apply_style()
        safe_update(self)

        if self._on_click_cmd:
            try:
                self._on_click_cmd()
            except Exception:
                pass

        page = get_control_page(self)
        if page:
            try:
                page.run_task(self._delayed_reset)
            except Exception:
                pass

    async def _delayed_reset(self) -> None:
        import asyncio
        await asyncio.sleep(0.85)
        self._is_confirmed = False
        self.scale = 1.0
        self._apply_style()
        safe_update(self)


class FletKineticEmergencyButton(ft.Container):
    """
    Botón de parada de emergencia [Alt+Q] con diseño táctico sobrio y mate.
    Utiliza glifo vectorial y dimensiones seguras para eliminar cualquier recorte.
    """

    def __init__(
        self,
        on_click: Callable[[], None],
        text: str = "SALIR [Alt+Q]",
        width: int = 124,
        height: int = 38,
        tooltip: str | None = "Detención incondicional y liberación de recursos [Left Alt + Q]"
    ) -> None:
        self._on_click_cmd = on_click
        self._icon_ctrl = ft.Icon(ft.Icons.POWER_SETTINGS_NEW_ROUNDED, size=14, color="#fca5a5")
        self._text_ctrl = ft.Text(
            value=text,
            size=12,
            weight=ft.FontWeight.BOLD,
            color="#fca5a5",
            text_align=ft.TextAlign.CENTER
        )

        super().__init__(
            content=ft.Row(
                controls=[self._icon_ctrl, self._text_ctrl],
                spacing=6,
                alignment=ft.MainAxisAlignment.CENTER,
                vertical_alignment=ft.CrossAxisAlignment.CENTER
            ),
            width=width,
            height=height,
            alignment=ft.Alignment(0, 0),
            bgcolor="#181012",
            border=ft.Border.all(1, "#b91c1c"),
            border_radius=8,
            tooltip=tooltip,
            animate=ft.Animation(140, ft.AnimationCurve.EASE_OUT),
            animate_scale=ft.Animation(120, ft.AnimationCurve.EASE_OUT),
            on_click=lambda e: self._on_click_cmd(),
            on_hover=self._handle_hover,
            ink=True,
            scale=1.0,
            shadow=None
        )

    def _handle_hover(self, e: ft.HoverEvent) -> None:
        is_hover = (e.data == "true")
        self.scale = 1.02 if is_hover else 1.0
        if is_hover:
            self.bgcolor = "#271216"
            self.border = ft.Border.all(1.2, "#ef4444")
            self._text_ctrl.color = "#ffffff"
            self._icon_ctrl.color = "#ffffff"
        else:
            self.bgcolor = "#181012"
            self.border = ft.Border.all(1, "#b91c1c")
            self._text_ctrl.color = "#fca5a5"
            self._icon_ctrl.color = "#fca5a5"
        self.shadow = None
        safe_update(self)
