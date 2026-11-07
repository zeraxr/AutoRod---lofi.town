"""Componente de Tarjeta Métrica para Flet (Diseño Oficial Figma 1:1)."""

from typing import Any
import flet as ft
from autorod.infrastructure.ui.flet.theme import ThemeManager, ThemeTokens
from autorod.infrastructure.ui.flet.utils import safe_update


class FletMetricCard(ft.Container):
    """
    Tarjeta métrica oficial Figma 1:1:
    - Línea 1: Título en mayúsculas sobrio (#8f99b3).
    - Línea 2: Valor nítido en blanco puro (#ffffff).
    - Sin bullets, sin subtítulos redundantes y sin botones invasivos.
    """

    def __init__(
        self,
        title: str,
        default_val: str,
        subtext: str = "",
        theme_manager: ThemeManager | None = None,
        action_control: ft.Control | None = None
    ) -> None:
        self._title = title
        self._val = default_val
        self._sub = subtext
        self._theme_mgr = theme_manager or ThemeManager.get_instance()
        self._theme: ThemeTokens = self._theme_mgr.current

        self._title_text = ft.Text(
            value=self._title.upper(),
            size=10,
            weight=ft.FontWeight.NORMAL,
            color="#a5b4ff" if self._theme.mode == "dark" else self._theme.text_muted
        )

        self._val_text = ft.Text(
            value=self._val,
            size=13,
            weight=ft.FontWeight.W_600,
            color="#ffffff" if self._theme.mode == "dark" else self._theme.text_primary
        )

        # Controles preservados internamente para compatibilidad de pruebas
        self._sub_text = ft.Text(value=self._sub, size=10, visible=False)
        self._dot = ft.Container(visible=False)

        super().__init__(
            content=ft.Column(
                controls=[
                    self._title_text,
                    self._val_text
                ],
                spacing=6,
                alignment=ft.MainAxisAlignment.START,
                horizontal_alignment=ft.CrossAxisAlignment.START
            ),
            bgcolor="#141a2a" if self._theme.mode == "dark" else "#ffffff",
            border=ft.Border.all(1, "#1b2233" if self._theme.mode == "dark" else "#e5e7eb"),
            border_radius=12,
            padding=ft.Padding.all(16),
            expand=True
        )

        self._theme_mgr.subscribe(self._on_theme_updated)

    def _on_theme_updated(self, tokens: ThemeTokens) -> None:
        self._theme = tokens
        self.bgcolor = "#141a2a" if tokens.mode == "dark" else "#ffffff"
        self.border = ft.Border.all(1, "#1b2233" if tokens.mode == "dark" else "#e5e7eb")
        self._title_text.color = "#a5b4ff" if tokens.mode == "dark" else tokens.text_muted
        self._val_text.color = "#ffffff" if tokens.mode == "dark" else tokens.text_primary
        safe_update(self)

    def update_val(self, val: str, color: str | None = None, sub: str | None = None) -> None:
        self._val = val
        self._val_text.value = val
        if color is not None:
            self._val_text.color = color
        else:
            self._val_text.color = "#ffffff" if self._theme.mode == "dark" else self._theme.text_primary
        if sub is not None:
            self._sub = sub
            self._sub_text.value = sub
        safe_update(self)
