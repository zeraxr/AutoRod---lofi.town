"""Componente de Tarjeta Métrica cinético reactivo al tema visual."""

import tkinter as tk
from typing import Any
from autorod.infrastructure.ui.tk.theme import ThemeManager, ThemeTokens
from autorod.infrastructure.ui.tk.components.glow_button import (
    _draw_rounded_polygon,
    _blend_color
)


class KineticMetricCard(tk.Canvas):
    """Tarjeta métrica con bordes redondeados, brillo superior y tipografía adaptativa."""

    def __init__(
        self,
        parent: tk.Widget,
        title: str,
        default_val: str,
        subtext: str,
        radius: int = 10,
        height: int = 76,
        theme_manager: ThemeManager | None = None
    ) -> None:
        super().__init__(
            parent,
            height=height,
            bg=parent.cget("bg"),
            highlightthickness=0
        )
        self._title = title
        self._val = default_val
        self._sub = subtext
        self._radius = radius
        self._height = height
        self._val_color = "#f3f4f6"
        self._use_theme_color = True

        self._theme_mgr = theme_manager or ThemeManager.get_instance()
        self._theme: ThemeTokens = self._theme_mgr.current
        self._theme_mgr.subscribe(self._on_theme_updated)

        self.bind("<Configure>", self._render)
        self.bind("<Destroy>", lambda e: self._theme_mgr.unsubscribe(self._on_theme_updated))

    def _on_theme_updated(self, tokens: ThemeTokens) -> None:
        self._theme = tokens
        if self.winfo_exists():
            self._render()

    def update_val(self, val: str, color: str | None = None, sub: str | None = None) -> None:
        self._val = val
        if color is not None:
            self._val_color = color
            self._use_theme_color = False
        else:
            self._use_theme_color = True
        if sub is not None:
            self._sub = sub
        self._render()

    def _render(self, event: Any = None) -> None:
        if not self.winfo_exists():
            return
        w = max(10, self.winfo_width())
        h = self._height
        self.delete("all")

        # Fondo con bordes redondeados y borde sutil
        _draw_rounded_polygon(
            self,
            2,
            2,
            w - 2,
            h - 2,
            radius=self._radius,
            fill="#11131c",
            outline="#1f2334",
            width=1
        )

        # Brillo superior sutil de cristal
        self.create_line(
            self._radius + 4,
            3,
            w - self._radius - 4,
            3,
            fill="#2c3149",
            width=1
        )

        val_col = self._theme.primary if self._use_theme_color else self._val_color

        # Punto de acento junto al título
        self.create_oval(
            14,
            14,
            18,
            18,
            fill=_blend_color("#11131c", val_col, 0.7, self),
            outline=""
        )

        # Título estilizado
        self.create_text(
            24,
            16,
            text=self._title,
            anchor="w",
            fill="#8b90a4",
            font=("Segoe UI", 7, "bold")
        )

        # Valor métrico principal
        self.create_text(
            14,
            38,
            text=self._val,
            anchor="w",
            fill=val_col,
            font=("Segoe UI", 12, "bold")
        )

        # Subtexto descriptivo
        self.create_text(
            14,
            58,
            text=self._sub,
            anchor="w",
            fill="#6d7388",
            font=("Segoe UI", 8)
        )
