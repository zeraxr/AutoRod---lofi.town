"""Componente de Tarjeta Métrica para Flet."""

from typing import Any
import flet as ft
from autorod.infrastructure.ui.flet.theme import ThemeManager, ThemeTokens
from autorod.infrastructure.ui.flet.utils import safe_update


class FletMetricCard(ft.Container):
    """Tarjeta métrica con diseño de cristal, brillo superior y tipografía reactiva."""

    def __init__(
        self,
        title: str,
        default_val: str,
        subtext: str,
        theme_manager: ThemeManager | None = None,
        action_control: ft.Control | None = None
    ) -> None:
        self._title = title
        self._val = default_val
        self._sub = subtext
        self._theme_mgr = theme_manager or ThemeManager.get_instance()
        self._theme: ThemeTokens = self._theme_mgr.current
        self._use_theme_color = True
        self._custom_val_color = "#f3f4f6"

        self._dot = ft.Container(
            width=6,
            height=6,
            border_radius=3,
            bgcolor=self._theme.primary
        )

        self._title_text = ft.Text(
            value=self._title,
            size=10,
            weight=ft.FontWeight.BOLD,
            color="#a1a1aa"
        )

        self._val_text = ft.Text(
            value=self._val,
            size=14,
            weight=ft.FontWeight.BOLD,
            color=self._theme.primary
        )

        self._sub_text = ft.Text(
            value=self._sub,
            size=10,
            color="#71717a"
        )

        header_row = ft.Row(
            controls=[
                ft.Row(controls=[self._dot, self._title_text], spacing=6),
                action_control if action_control else ft.Container()
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER
        )

        super().__init__(
            content=ft.Column(
                controls=[
                    header_row,
                    self._val_text,
                    self._sub_text
                ],
                spacing=3,
                alignment=ft.MainAxisAlignment.CENTER
            ),
            bgcolor="#14151c",
            border=ft.Border.all(1, "#1e1f29"),
            border_radius=8,
            padding=ft.Padding.symmetric(horizontal=12, vertical=10),
            animate=ft.Animation(160, ft.AnimationCurve.EASE_OUT)
        )

        self._theme_mgr.subscribe(self._on_theme_updated)

    def _on_theme_updated(self, tokens: ThemeTokens) -> None:
        self._theme = tokens
        self._dot.bgcolor = tokens.primary
        if self._use_theme_color:
            self._val_text.color = tokens.primary
        safe_update(self)

    def update_val(self, val: str, color: str | None = None, sub: str | None = None) -> None:
        self._val = val
        self._val_text.value = val

        if color is not None:
            self._use_theme_color = False
            self._custom_val_color = color
            self._val_text.color = color
        else:
            self._use_theme_color = True
            self._val_text.color = self._theme.primary

        if sub is not None:
            self._sub = sub
            self._sub_text.value = sub

        safe_update(self)
