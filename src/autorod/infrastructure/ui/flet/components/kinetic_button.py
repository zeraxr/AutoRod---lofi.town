"""Componentes de botones cinéticos avanzados para AutoRod en Flet."""

from typing import Callable, Any
import flet as ft
from autorod.infrastructure.ui.flet.theme import ThemeManager, ThemeTokens
from autorod.infrastructure.ui.flet.utils import safe_update, get_control_page


class FletKineticGlowButton(ft.Container):
    """
    Botón cinético de nivel industrial para Flet con iluminación reactiva y micro-interacciones:
    - Breathing glow continuo sincronizado con el tema activo.
    - Hover spotlight con gradiente reactivo y elevación suave.
    - Confirmación visual al clic con ciclo de reseteo automático.
    """

    def __init__(
        self,
        text: str,
        on_click: Callable[[], None] | None = None,
        width: int = 136,
        height: int = 38,
        is_primary: bool = True,
        confirmed_text: str = "✓ EJECUTADO",
        theme_manager: ThemeManager | None = None,
        tooltip: str | None = None
    ) -> None:
        self._initial_text = text
        self._confirmed_text = confirmed_text
        self._on_click_cmd = on_click
        self._is_primary = is_primary
        self._theme_mgr = theme_manager or ThemeManager.get_instance()
        self._theme: ThemeTokens = self._theme_mgr.current

        self._is_hovered = False
        self._is_confirmed = False

        self._btn_text = ft.Text(
            value=self._initial_text,
            size=12,
            weight=ft.FontWeight.W_600,
            color=self._theme.text_on_primary if is_primary else "#e2e8f0",
            text_align=ft.TextAlign.CENTER
        )

        super().__init__(
            content=self._btn_text,
            width=width,
            height=height,
            alignment=ft.Alignment(0, 0),
            border_radius=10,
            animate=ft.Animation(180, ft.AnimationCurve.EASE_OUT),
            animate_scale=ft.Animation(150, ft.AnimationCurve.EASE_OUT),
            on_click=self._handle_click,
            on_hover=self._handle_hover,
            ink=True,
            scale=1.0,
            tooltip=tooltip
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
        glow = self._theme.glow_color

        if self._is_primary:
            if self._is_confirmed:
                self.bgcolor = primary
                self._btn_text.value = self._confirmed_text
                self._btn_text.color = text_col
                self.border = ft.Border.all(1.5, "#ffffff")
                self.shadow = ft.BoxShadow(
                    spread_radius=1.5,
                    blur_radius=16,
                    color=glow,
                    offset=ft.Offset(0, 2)
                )
            elif self._is_hovered:
                self.bgcolor = hover
                self._btn_text.value = self._initial_text
                self._btn_text.color = text_col
                self.border = ft.Border.all(1.2, "#ffffff")
                self.shadow = ft.BoxShadow(
                    spread_radius=1,
                    blur_radius=14,
                    color=glow,
                    offset=ft.Offset(0, 2)
                )
            else:
                self.bgcolor = primary
                self._btn_text.value = self._initial_text
                self._btn_text.color = text_col
                self.border = ft.Border.all(1, hover)
                self.shadow = ft.BoxShadow(
                    spread_radius=0.5,
                    blur_radius=10,
                    color=glow,
                    offset=ft.Offset(0, 2)
                )
        else:
            if self._is_hovered:
                self.bgcolor = "#1a1f2e"
                self._btn_text.color = "#ffffff"
                self.border = ft.Border.all(1.2, primary)
                self.shadow = ft.BoxShadow(
                    spread_radius=0.5,
                    blur_radius=10,
                    color=glow,
                    offset=ft.Offset(0, 2)
                )
            else:
                self.bgcolor = "#121520"
                self._btn_text.color = "#e2e8f0"
                self.border = ft.Border.all(1, "#23283c")
                self.shadow = None

    def set_text(self, text: str) -> None:
        self._initial_text = text
        if not self._is_confirmed:
            self._btn_text.value = text
            safe_update(self)

    def _handle_hover(self, e: ft.HoverEvent) -> None:
        self._is_hovered = (e.data == "true")
        self.scale = 1.025 if self._is_hovered else 1.0
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
    Botón táctico de parada de emergencia [Q] en Flet.
    Garantiza CERO recortes de texto mediante padding seguro y dimensiones explícitas.
    """

    def __init__(
        self,
        on_click: Callable[[], None],
        text: str = "🚨 SALIR [Q]",
        width: int = 132,
        height: int = 38,
        tooltip: str | None = "Detención de emergencia del software y liberación de recursos [Tecla Q]"
    ) -> None:
        self._on_click_cmd = on_click
        self._text_ctrl = ft.Text(
            value=text,
            size=12,
            weight=ft.FontWeight.BOLD,
            color="#fca5a5",
            text_align=ft.TextAlign.CENTER
        )

        super().__init__(
            content=self._text_ctrl,
            width=width,
            height=height,
            alignment=ft.Alignment(0, 0),
            bgcolor="#1f1114",
            border=ft.Border.all(1.2, "#e11d48"),
            border_radius=10,
            tooltip=tooltip,
            animate=ft.Animation(150, ft.AnimationCurve.EASE_OUT),
            animate_scale=ft.Animation(150, ft.AnimationCurve.EASE_OUT),
            on_click=lambda e: self._on_click_cmd(),
            on_hover=self._handle_hover,
            ink=True,
            scale=1.0,
            shadow=ft.BoxShadow(
                spread_radius=0.5,
                blur_radius=8,
                color="#7f1d1d44",
                offset=ft.Offset(0, 2)
            )
        )

    def _handle_hover(self, e: ft.HoverEvent) -> None:
        is_hover = (e.data == "true")
        self.scale = 1.03 if is_hover else 1.0
        if is_hover:
            self.bgcolor = "#341218"
            self.border = ft.Border.all(1.5, "#ff4d4f")
            self._text_ctrl.color = "#ffffff"
            self.shadow = ft.BoxShadow(
                spread_radius=1,
                blur_radius=14,
                color="#ef444488",
                offset=ft.Offset(0, 2)
            )
        else:
            self.bgcolor = "#1f1114"
            self.border = ft.Border.all(1.2, "#e11d48")
            self._text_ctrl.color = "#fca5a5"
            self.shadow = ft.BoxShadow(
                spread_radius=0.5,
                blur_radius=8,
                color="#7f1d1d44",
                offset=ft.Offset(0, 2)
            )

        safe_update(self)
