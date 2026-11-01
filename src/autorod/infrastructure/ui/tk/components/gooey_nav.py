"""Barra lateral colapsable con navegación líquida (Gooey Bubble Tab Navigation).

Especificación del usuario:
- "El dashboard, debe ser desplegable al seleccionar el ícono de la aplicación, desplegado con el ícono y el nombre de la aplicación, al presionarlo, se esconde y sólo quedan los íconos visibles en el dashboard, el presionarlos, el usuario navega entre las pestañas."
- "Dashboard: A gooey bubble flows between tabs, flooding the screen with an animation."
- "El software debe ser manejado todo en el mismo programa, por ejemplo cuando abres el apartado de colores, se abre otra ventana, innecesario."

Características:
- Cabecera interactiva con logotipo oficial, indicador de estado online en vivo y conmutador [◀ / ▶].
- Conmutación suave entre modo expandido (210px) y compacto/colapsado (68px).
- Burbuja líquida con física viscoelástica (Squash & Stretch) y amortiguación elástica de resorte.
- Onda de inundación (screen flood animation) al llegar a la pestaña de destino.
- Selección de paleta de colores integrada directamente como pestaña en la misma ventana.
- Sincronización instantánea con ThemeManager.
"""

import math
import tkinter as tk
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
    return 12, 13, 16


def _blend_color(hex1: str, hex2: str, factor: float, canvas: tk.Canvas | None = None) -> str:
    factor = max(0.0, min(1.0, factor))
    r1, g1, b1 = _color_to_rgb(canvas, hex1)
    r2, g2, b2 = _color_to_rgb(canvas, hex2)
    r = int(r1 + (r2 - r1) * factor)
    g = int(g1 + (g2 - g1) * factor)
    b = int(b1 + (b2 - b1) * factor)
    return f"#{r:02x}{g:02x}{b:02x}"


class CollapsibleGooeySidebar(tk.Frame):
    """Barra lateral inteligente con colapso de acordeón y selector de pestañas gooey."""

    TAB_ITEMS = [
        ("dashboard", "🖥️", "Visor / Dashboard"),
        ("settings", "⚙️", "Configuración"),
        ("palette", "🎨", "Personalizar Colores"),
        ("telemetry", "📊", "Telemetría / Logs"),
    ]

    EXPANDED_WIDTH = 210
    COLLAPSED_WIDTH = 68
    TAB_HEIGHT = 44
    TAB_SPACING = 8

    def __init__(
        self,
        parent: tk.Widget,
        on_tab_selected: Callable[[str], None],
        logo_image: tk.PhotoImage | None = None,
        theme_manager: ThemeManager | None = None
    ) -> None:
        super().__init__(parent, bg="#0f1118", width=self.EXPANDED_WIDTH)
        self.pack_propagate(False)

        self._on_tab_selected = on_tab_selected
        self._logo_image = logo_image
        self._theme_mgr = theme_manager or ThemeManager.get_instance()
        self._theme: ThemeTokens = self._theme_mgr.current

        self._is_collapsed = False
        self._active_tab = "dashboard"

        # Física de la burbuja Gooey
        self._bubble_current_y = 12.0
        self._bubble_target_y = 12.0
        self._bubble_animating = False
        self._anim_timer_id: str | None = None

        # Onda expansiva de inundación (Screen flood animation)
        self._flood_active = False
        self._flood_progress = 0.0
        self._flood_y = 12.0

        # Pulso sutil del indicador de estado
        self._pulse_phase = 0.0
        self._pulse_timer_id: str | None = None

        self._theme_mgr.subscribe(self._on_theme_updated)

        self._build_components()

        self._bubble_current_y = self._get_tab_y(self._active_tab)
        self._bubble_target_y = self._bubble_current_y
        self._render_tabs()
        self._start_status_pulse()

    def _on_theme_updated(self, tokens: ThemeTokens) -> None:
        self._theme = tokens
        if self.winfo_exists():
            self._render_header()
            self._render_tabs()

    def _build_components(self) -> None:
        """Construye la cabecera interactiva y el Canvas de pestañas."""
        # 1. Cabecera con Icono y Nombre de la Aplicación
        self._header_card = tk.Canvas(
            self,
            height=68,
            bg="#0f1118",
            highlightthickness=0,
            cursor="hand2"
        )
        self._header_card.pack(fill=tk.X, side=tk.TOP, pady=(6, 4))
        self._header_card.bind("<Button-1>", lambda e: self.toggle_collapsed())
        self._header_card.bind("<Configure>", lambda e: self._render_header())

        # Separador horizontal suave
        self._sep = tk.Frame(self, bg="#1c1f2b", height=1)
        self._sep.pack(fill=tk.X, padx=12, pady=(2, 10))

        # 2. Canvas Unificado para el Gooey Nav Rail
        self._nav_canvas = tk.Canvas(
            self,
            bg="#0f1118",
            highlightthickness=0,
            cursor="hand2"
        )
        self._nav_canvas.pack(fill=tk.BOTH, expand=True, padx=6)
        self._nav_canvas.bind("<Button-1>", self._on_canvas_click)
        self._nav_canvas.bind("<Configure>", lambda e: self._render_tabs())

    def _start_status_pulse(self) -> None:
        """Pulso visual continuo para el punto de estado del sistema."""
        if not self.winfo_exists():
            return
        self._pulse_phase += 0.10
        if self._pulse_phase > 2 * math.pi:
            self._pulse_phase -= 2 * math.pi
        self._render_header()
        self._pulse_timer_id = self.after(50, self._start_status_pulse)

    # -------------------------------------------------------------------------
    # COLAPSO Y EXPANSIÓN
    # -------------------------------------------------------------------------
    def toggle_collapsed(self) -> None:
        """Alterna entre expandido (210px) y colapsado (68px)."""
        self._is_collapsed = not self._is_collapsed
        new_width = self.COLLAPSED_WIDTH if self._is_collapsed else self.EXPANDED_WIDTH
        self.config(width=new_width)
        self._render_header()
        self._render_tabs()

    def _render_header(self) -> None:
        if not self.winfo_exists():
            return
        self._header_card.delete("all")
        w = self._header_card.winfo_width() or (self.COLLAPSED_WIDTH if self._is_collapsed else self.EXPANDED_WIDTH)

        pulse_alpha = 0.5 + 0.5 * math.sin(self._pulse_phase)
        dot_color = _blend_color("#238636", "#3ecf8e", pulse_alpha, self._header_card)

        if self._is_collapsed:
            # Modo icono centrado compacto
            _draw_rounded_polygon(
                self._header_card,
                10,
                10,
                w - 10,
                58,
                radius=12,
                fill="#161822",
                outline="#232738",
                width=1
            )
            if self._logo_image:
                self._header_card.create_image(w // 2, 34, image=self._logo_image)
            else:
                self._header_card.create_text(w // 2, 34, text="🎣", font=("Segoe UI", 16))

            # Punto de estado en la esquina del icono
            self._header_card.create_oval(w - 22, 14, w - 16, 20, fill=dot_color, outline="")
        else:
            # Modo expandido: Icono + Nombre "AutoRod" + Pulsing Dot + Chevron
            _draw_rounded_polygon(
                self._header_card,
                8,
                8,
                52,
                58,
                radius=10,
                fill="#161822",
                outline="#232738",
                width=1
            )
            if self._logo_image:
                self._header_card.create_image(30, 33, image=self._logo_image)
            else:
                self._header_card.create_text(30, 33, text="🎣", font=("Segoe UI", 14))

            # Título AutoRod
            self._header_card.create_text(
                62,
                24,
                text="AutoRod",
                anchor="w",
                fill="#ffffff",
                font=("Segoe UI", 11, "bold")
            )

            # Punto de estado verde online
            self._header_card.create_oval(122, 21, 128, 27, fill=dot_color, outline="")

            # Tag de versión / Tema
            self._header_card.create_text(
                62,
                42,
                text="Visual Automation",
                anchor="w",
                fill=self._theme.primary,
                font=("Segoe UI", 8, "bold")
            )

            # Chevron de colapso a la derecha
            self._header_card.create_text(
                w - 16,
                33,
                text="◀",
                fill="#64748b",
                font=("Segoe UI", 8)
            )

    # -------------------------------------------------------------------------
    # MATEMÁTICA Y FÍSICA DE LA BURBUJA GOOEY
    # -------------------------------------------------------------------------
    def _get_tab_y(self, tab_id: str) -> float:
        for idx, (tid, _, _) in enumerate(self.TAB_ITEMS):
            if tid == tab_id:
                return float(10 + idx * (self.TAB_HEIGHT + self.TAB_SPACING))
        return 10.0

    def select_tab(self, tab_id: str) -> None:
        """Selecciona una pestaña y anima suavemente la burbuja líquida."""
        self._active_tab = tab_id
        self._bubble_target_y = self._get_tab_y(tab_id)

        if not self._bubble_animating:
            self._bubble_animating = True
            self._step_gooey_bubble()

        # Notificar al coordinador de la app (100% en la misma ventana)
        self._on_tab_selected(tab_id)

    def _step_gooey_bubble(self) -> None:
        if not self.winfo_exists():
            return

        diff = self._bubble_target_y - self._bubble_current_y
        if abs(diff) < 0.6:
            self._bubble_current_y = self._bubble_target_y
            self._bubble_animating = False
            self._trigger_flood_pulse(self._bubble_target_y)
            self._render_tabs()
            return

        # Amortiguación elástica de resorte
        self._bubble_current_y += diff * 0.28
        self._render_tabs()

        self._anim_timer_id = self.after(16, self._step_gooey_bubble)

    def _trigger_flood_pulse(self, y: float) -> None:
        self._flood_active = True
        self._flood_progress = 0.0
        self._flood_y = y
        self._step_flood_pulse()

    def _step_flood_pulse(self) -> None:
        if not self.winfo_exists() or not self._flood_active:
            return

        self._flood_progress += 0.16
        if self._flood_progress >= 1.0:
            self._flood_active = False
            self._flood_progress = 0.0
            self._render_tabs()
            return

        self._render_tabs()
        self.after(20, self._step_flood_pulse)

    # -------------------------------------------------------------------------
    # RENDERIZADO DE PESTAÑAS Y BURBUJA LÍQUIDA
    # -------------------------------------------------------------------------
    def _render_tabs(self) -> None:
        if not self.winfo_exists():
            return

        self._nav_canvas.delete("all")
        w = max(10, self._nav_canvas.winfo_width())

        # 1. Dibujar la Burbuja Gooey (Líquida)
        by = self._bubble_current_y
        diff = abs(self._bubble_target_y - self._bubble_current_y)
        stretch_y = min(14.0, diff * 0.35) if self._bubble_animating else 0.0

        bubble_top = by - stretch_y / 2
        bubble_bottom = by + self.TAB_HEIGHT + stretch_y / 2

        # Relleno con acento sutil
        _draw_rounded_polygon(
            self._nav_canvas,
            4,
            bubble_top,
            w - 4,
            bubble_bottom,
            radius=10,
            fill=self._theme.accent_subtle,
            outline=self._theme.border_active,
            width=1,
            tags="gooey_bubble"
        )

        # Barra indicadora lateral izquierda de la burbuja
        self._nav_canvas.create_line(
            8,
            bubble_top + 10,
            8,
            bubble_bottom - 10,
            fill=self._theme.primary,
            width=3,
            capstyle=tk.ROUND,
            tags="gooey_indicator"
        )

        # 2. Onda expansiva de inundación (Screen flood animation)
        if self._flood_active:
            fy = self._flood_y + self.TAB_HEIGHT / 2
            fx = w / 2
            max_r = w * 0.85
            curr_r = max_r * self._flood_progress
            alpha_blend = _blend_color(
                self._theme.accent_subtle,
                self._theme.primary,
                0.45 * (1.0 - self._flood_progress),
                self._nav_canvas
            )

            self._nav_canvas.create_oval(
                fx - curr_r,
                fy - curr_r * 0.45,
                fx + curr_r,
                fy + curr_r * 0.45,
                fill=alpha_blend,
                outline="",
                tags="tab_flood"
            )

        # 3. Dibujar iconos y textos de cada pestaña
        for idx, (tid, icon, label) in enumerate(self.TAB_ITEMS):
            ty = 10 + idx * (self.TAB_HEIGHT + self.TAB_SPACING)
            is_active = (tid == self._active_tab)

            icon_col = self._theme.primary if is_active else "#848999"
            text_col = "#ffffff" if is_active else "#9da1b0"
            font_weight = "bold" if is_active else "normal"

            if self._is_collapsed:
                # Solo icono centrado
                self._nav_canvas.create_text(
                    w // 2,
                    ty + self.TAB_HEIGHT // 2,
                    text=icon,
                    font=("Segoe UI Emoji", 13),
                    fill=icon_col,
                    tags=f"tab_{tid}"
                )
            else:
                # Icono a la izquierda y texto a la derecha
                self._nav_canvas.create_text(
                    22,
                    ty + self.TAB_HEIGHT // 2,
                    text=icon,
                    font=("Segoe UI Emoji", 12),
                    fill=icon_col,
                    tags=f"tab_{tid}"
                )
                self._nav_canvas.create_text(
                    42,
                    ty + self.TAB_HEIGHT // 2,
                    text=label,
                    anchor="w",
                    font=("Segoe UI", 9, font_weight),
                    fill=text_col,
                    tags=f"tab_{tid}"
                )

    def _on_canvas_click(self, event: tk.Event[Any]) -> None:
        cy = event.y
        for idx, (tid, _, _) in enumerate(self.TAB_ITEMS):
            ty = 10 + idx * (self.TAB_HEIGHT + self.TAB_SPACING)
            if ty <= cy <= ty + self.TAB_HEIGHT:
                self.select_tab(tid)
                break

    def destroy(self) -> None:
        self._theme_mgr.unsubscribe(self._on_theme_updated)
        if self._pulse_timer_id is not None:
            try:
                self.after_cancel(self._pulse_timer_id)
            except Exception:
                pass
        super().destroy()
