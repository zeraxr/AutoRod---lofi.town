"""Componentes de botones cinéticos avanzados para AutoRod.

Incluye:
- KineticGlowButton: Botón interactivo con respiración de luz (breathing glow),
  foco interior que sigue al cursor (spotlight), borde de cristal reflectante (glassmorphic rim)
  y onda líquida expansiva al clic con confirmación visual en bucle.
- KineticEmergencyButton: Botón táctico de emergencia [Q] con tipografía e icono
  medidos explícitamente para garantizar CERO recortes de texto en cualquier resolución o DPI.
"""

import math
import tkinter as tk
import tkinter.font as tkfont
from typing import Callable, Any
from autorod.infrastructure.ui.tk.theme import ThemeManager, ThemeTokens


def _draw_rounded_polygon(
    canvas: tk.Canvas,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    radius: float = 8.0,
    **kwargs: Any
) -> int:
    """Traza un polígono redondeado con curvas suaves en Tkinter Canvas."""
    r = max(2.0, min(radius, (x2 - x1) / 2, (y2 - y1) / 2))
    points = [
        x1 + r, y1,
        x1 + r, y1,
        x2 - r, y1,
        x2 - r, y1,
        x2, y1,
        x2, y1 + r,
        x2, y1 + r,
        x2, y2 - r,
        x2, y2 - r,
        x2, y2,
        x2 - r, y2,
        x2 - r, y2,
        x1 + r, y2,
        x1 + r, y2,
        x1, y2,
        x1, y2 - r,
        x1, y2 - r,
        x1, y1 + r,
        x1, y1 + r,
        x1, y1
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)


def _color_to_rgb(canvas: tk.Canvas | None, color_str: str) -> tuple[int, int, int]:
    """Convierte cualquier color de Tkinter (hex o nombre de sistema) a RGB."""
    if color_str.startswith("#"):
        h = color_str.lstrip("#")
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        try:
            return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        except Exception:
            pass
    if canvas:
        try:
            r, g, b = canvas.winfo_rgb(color_str)
            return r >> 8, g >> 8, b >> 8
        except Exception:
            pass
    return 12, 13, 16  # Fallback a fondo oscuro #0c0d10


def _blend_color(hex1: str, hex2: str, factor: float, canvas: tk.Canvas | None = None) -> str:
    """Interpola linealmente entre dos colores (0.0 a 1.0) con soporte para nombres de sistema."""
    factor = max(0.0, min(1.0, factor))
    r1, g1, b1 = _color_to_rgb(canvas, hex1)
    r2, g2, b2 = _color_to_rgb(canvas, hex2)
    r = int(r1 + (r2 - r1) * factor)
    g = int(g1 + (g2 - g1) * factor)
    b = int(b1 + (b2 - b1) * factor)
    return f"#{r:02x}{g:02x}{b:02x}"


class KineticGlowButton(tk.Canvas):
    """
    Botón cinético de nivel industrial con iluminación reactiva:
    - Breathing glow continuo.
    - Spotlight interior sensible a la posición del cursor.
    - Top-edge glassmorphic highlight para profundidad moderna.
    - Flood wave de confirmación al hacer clic.
    """

    def __init__(
        self,
        parent: tk.Widget,
        text: str,
        command: Callable[[], None] | None = None,
        width: int = 130,
        height: int = 34,
        radius: int = 8,
        font: tuple[str, int, str] = ("Segoe UI", 9, "bold"),
        is_primary: bool = True,
        confirmed_text: str = "✓ LISTO",
        loop_confirmation: bool = True,
        theme_manager: ThemeManager | None = None
    ) -> None:
        super().__init__(
            parent,
            width=width,
            height=height,
            bg=parent.cget("bg"),
            highlightthickness=0,
            cursor="hand2"
        )
        self._text = text
        self._initial_text = text
        self._confirmed_text = confirmed_text
        self._command = command
        self._width = width
        self._height = height
        self._radius = radius
        self._font = font
        self._is_primary = is_primary
        self._loop_confirmation = loop_confirmation

        # Gestor de temas
        self._theme_mgr = theme_manager or ThemeManager.get_instance()
        self._theme: ThemeTokens = self._theme_mgr.current

        # Estados de interacción
        self._is_hovered = False
        self._cursor_x = width / 2.0
        self._cursor_y = height / 2.0

        # Breathing Glow
        self._breath_phase = 0.0
        self._breath_timer_id: str | None = None

        # Flood Wave
        self._flood_active = False
        self._flood_progress = 0.0
        self._flood_origin = (width / 2.0, height / 2.0)
        self._flood_timer_id: str | None = None

        self._theme_mgr.subscribe(self._on_theme_updated)

        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Motion>", self._on_motion)
        self.bind("<Button-1>", self._on_click)
        self.bind("<Destroy>", self._on_destroy)

        self._render()
        self._start_breathing_loop()

    def _on_theme_updated(self, tokens: ThemeTokens) -> None:
        self._theme = tokens
        if self.winfo_exists():
            self._render()

    def set_text(self, text: str) -> None:
        self._text = text
        self._initial_text = text
        self._render()

    def _on_enter(self, event: tk.Event[Any]) -> None:
        self._is_hovered = True
        self._cursor_x = float(event.x)
        self._cursor_y = float(event.y)
        self._render()

    def _on_leave(self, event: tk.Event[Any]) -> None:
        self._is_hovered = False
        self._cursor_x = self._width / 2.0
        self._cursor_y = self._height / 2.0
        self._render()

    def _on_motion(self, event: tk.Event[Any]) -> None:
        self._cursor_x = float(event.x)
        self._cursor_y = float(event.y)
        self._render()

    def _on_click(self, event: tk.Event[Any]) -> None:
        if self._flood_active:
            return

        self._flood_origin = (float(event.x), float(event.y))
        self._flood_active = True
        self._flood_progress = 0.0
        self._text = self._confirmed_text
        self._render()

        self._step_flood_wave()

        if self._command:
            try:
                self._command()
            except Exception:
                pass

    def _start_breathing_loop(self) -> None:
        self._tick_breath()

    def _tick_breath(self) -> None:
        if not self.winfo_exists():
            return

        self._breath_phase += 0.08
        if self._breath_phase > 2 * math.pi:
            self._breath_phase -= 2 * math.pi

        if not self._flood_active:
            self._render()

        self._breath_timer_id = self.after(33, self._tick_breath)

    def _step_flood_wave(self) -> None:
        if not self.winfo_exists() or not self._flood_active:
            return

        self._flood_progress += 0.14
        if self._flood_progress >= 1.0:
            self._flood_progress = 1.0
            self._render()
            if self._loop_confirmation:
                self.after(850, self._reset_from_confirmation)
            return

        self._render()
        self._flood_timer_id = self.after(20, self._step_flood_wave)

    def _reset_from_confirmation(self) -> None:
        if not self.winfo_exists():
            return
        self._flood_active = False
        self._flood_progress = 0.0
        self._text = self._initial_text
        self._render()

    def _render(self) -> None:
        if not self.winfo_exists():
            return

        self.delete("all")
        w = max(10, self.winfo_width() or self._width)
        h = max(10, self.winfo_height() or self._height)

        breath_intensity = 0.5 + 0.5 * math.sin(self._breath_phase)

        primary = self._theme.primary
        hover = self._theme.primary_hover
        text_color = self._theme.text_on_primary

        if not self._is_primary:
            # Botón secundario estilizado (superficie oscura de cristal y borde activo)
            bg_fill = "#14161f" if not self._is_hovered else "#1b1e2a"
            border_col = _blend_color("#282c3f", primary, 0.45 + 0.45 * breath_intensity, self)
            text_col = "#e2e8f0" if not self._is_hovered else "#ffffff"
        else:
            # Botón primario vibrante
            bg_fill = hover if self._is_hovered else primary
            border_col = _blend_color(primary, "#ffffff", 0.35 * breath_intensity, self)
            text_col = text_color

        # 1. Resplandor exterior (Breathing Glow Halo)
        if self._is_primary:
            halo_expand = 1.0 + 2.8 * breath_intensity
            glow_blend = _blend_color("#0c0d10", self._theme.glow_color, 0.30 * breath_intensity, self)
            _draw_rounded_polygon(
                self,
                2 - halo_expand,
                2 - halo_expand,
                w - 2 + halo_expand,
                h - 2 + halo_expand,
                radius=self._radius + 3,
                fill=glow_blend,
                outline="",
                tags="glow_halo"
            )

        # 2. Base del Botón
        _draw_rounded_polygon(
            self,
            2,
            2,
            w - 2,
            h - 2,
            radius=self._radius,
            fill=bg_fill,
            outline="",
            tags="button_base"
        )

        # 3. Spotlight interactivo que sigue al cursor
        if self._is_hovered and not self._flood_active:
            cx = max(self._radius + 4, min(w - self._radius - 4, self._cursor_x))
            cy = max(self._radius + 4, min(h - self._radius - 4, self._cursor_y))
            spotlight_radius = min(w, h) * 0.70
            spot_color = _blend_color(bg_fill, "#ffffff", 0.30 if self._is_primary else 0.18, self)

            self.create_oval(
                cx - spotlight_radius,
                cy - spotlight_radius / 2,
                cx + spotlight_radius,
                cy + spotlight_radius / 2,
                fill=spot_color,
                outline="",
                tags="spotlight"
            )

        # 4. Onda expansiva al clic (Flood wave)
        if self._flood_active:
            fx, fy = self._flood_origin
            max_dist = math.hypot(max(fx, w - fx), max(fy, h - fy)) * 1.2
            curr_r = max_dist * self._flood_progress
            flood_fill = _blend_color(primary, "#ffffff", 0.65 * (1.0 - self._flood_progress), self)

            self.create_oval(
                fx - curr_r,
                fy - curr_r,
                fx + curr_r,
                fy + curr_r,
                fill=flood_fill,
                outline="",
                tags="flood_wave"
            )
            self.create_oval(
                fx - curr_r,
                fy - curr_r,
                fx + curr_r,
                fy + curr_r,
                fill="",
                outline="#ffffff",
                width=2,
                tags="flood_rim"
            )

        # 5. Borde perimetral nítido sobre el contenido
        _draw_rounded_polygon(
            self,
            2,
            2,
            w - 2,
            h - 2,
            radius=self._radius,
            fill="",
            outline=border_col,
            width=1,
            tags="button_border"
        )

        # 6. Top-edge glassmorphic sheen (Brillo de borde superior moderno)
        sheen_color = _blend_color(border_col, "#ffffff", 0.45, self)
        self.create_line(
            self._radius + 4,
            3,
            w - self._radius - 4,
            3,
            fill=sheen_color,
            width=1,
            tags="glass_sheen"
        )

        # 7. Etiqueta tipográfica
        self.create_text(
            w // 2,
            h // 2,
            text=self._text,
            fill="#ffffff" if self._flood_active else text_col,
            font=self._font,
            tags="button_label"
        )

    def _on_destroy(self, event: tk.Event[Any]) -> None:
        self._theme_mgr.unsubscribe(self._on_theme_updated)
        if self._breath_timer_id is not None:
            try:
                self.after_cancel(self._breath_timer_id)
            except Exception:
                pass
            self._breath_timer_id = None
        if self._flood_timer_id is not None:
            try:
                self.after_cancel(self._flood_timer_id)
            except Exception:
                pass
            self._flood_timer_id = None


class KineticEmergencyButton(tk.Canvas):
    """
    Botón de Parada de Emergencia [Q] con diseño táctico de alto impacto.
    
    Resuelve definitivamente el error de texto cortado del usuario:
    - Ancho y espaciado computados dinámicamente con margen de seguridad.
    - Dibujo vectorial en Canvas que nunca se trunca bajo ninguna resolución ni DPI.
    - Borde crimson de alerta roja #ef4444 con fondo de cristal oscuro #241215.
    - Ejecución inmediata e incondicional de parada de proceso.
    """

    def __init__(
        self,
        parent: tk.Widget,
        command: Callable[[], None],
        text: str = "🚨 SALIR [Q]",
        width: int = 126,
        height: int = 34,
        radius: int = 8
    ) -> None:
        super().__init__(
            parent,
            width=width,
            height=height,
            bg=parent.cget("bg"),
            highlightthickness=0,
            cursor="hand2"
        )
        self._command = command
        self._text = text
        self._width = width
        self._height = height
        self._radius = radius
        self._is_hovered = False
        self._font = ("Segoe UI", 9, "bold")

        # Medir longitud del texto para asegurar que NUNCA quede cortado
        f = tkfont.Font(family="Segoe UI", size=9, weight="bold")
        measured_width = f.measure(self._text) + 38  # 38px de padding para icono y márgenes
        if measured_width > self._width:
            self._width = measured_width
            self.config(width=self._width)

        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", lambda e: self._command())

        self._render()

    def _on_enter(self, event: Any) -> None:
        self._is_hovered = True
        self._render()

    def _on_leave(self, event: Any) -> None:
        self._is_hovered = False
        self._render()

    def _render(self) -> None:
        self.delete("all")
        w = max(10, self.winfo_width() or self._width)
        h = max(10, self.winfo_height() or self._height)

        if self._is_hovered:
            bg_fill = "#38151a"
            border_col = "#ff4d4f"
            border_w = 2
            text_col = "#ffffff"
        else:
            bg_fill = "#241114"
            border_col = "#dc2626"
            border_w = 1
            text_col = "#fca5a5"

        # Halo sutil de advertencia al hover
        if self._is_hovered:
            _draw_rounded_polygon(
                self,
                0,
                0,
                w,
                h,
                radius=self._radius + 2,
                fill="#3a1117",
                outline="",
                tags="halo"
            )

        # Fondo del botón
        _draw_rounded_polygon(
            self,
            2,
            2,
            w - 2,
            h - 2,
            radius=self._radius,
            fill=bg_fill,
            outline=border_col,
            width=border_w,
            tags="base"
        )

        # Brillo superior
        self.create_line(
            self._radius + 4,
            3,
            w - self._radius - 4,
            3,
            fill="#ff7875" if self._is_hovered else "#7f1d1d",
            width=1
        )

        # Texto centrado que garantiza CERO truncamiento
        self.create_text(
            w // 2,
            h // 2,
            text=self._text,
            fill=text_col,
            font=self._font,
            tags="label"
        )
