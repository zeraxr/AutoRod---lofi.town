"""Modal y panel interactivo para la personalización de colores de la UI.

Permite seleccionar entre los 6 esquemas predefinidos especificados:
1. "Botones por defecto" (Supabase Emerald #3ECF8E)
2. "Botones en blanco" (Minimalista #FFFFFF)
3. "Botones en colores rojo" (Cyberpunk #EF4444)
4. "Botones en verde color github" (GitHub Primer #238636)
5. "Botón en morado" (Neon Violet #8B5CF6)
6. "Botón en celeste" (Electric Sky #38BDF8)

Incluye:
- Tarjetas de muestra con halo y ratio de contraste WCAG 2.2.
- Aplicación reactiva instantánea a través de ThemeManager.
- Persistencia automática en config.toml sin reiniciar.
"""

import tkinter as tk
from typing import Callable, Any
from autorod.infrastructure.ui.tk.theme import ThemeManager, ThemeTokens, THEME_PRESETS
from autorod.config import AppConfig, save_config


def _draw_rounded_polygon(
    canvas: tk.Canvas,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    radius: float = 8.0,
    **kwargs: Any
) -> int:
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


class ThemeOptionCard(tk.Canvas):
    """Fila interactiva para la selección de cada tema con métricas WCAG 2.2."""

    def __init__(
        self,
        parent: tk.Widget,
        tokens: ThemeTokens,
        is_active: bool,
        on_select: Callable[[str], None]
    ) -> None:
        super().__init__(
            parent,
            height=52,
            bg="#131418",
            highlightthickness=0,
            cursor="hand2"
        )
        self._tokens = tokens
        self._is_active = is_active
        self._on_select = on_select
        self._is_hovered = False

        self.bind("<Configure>", lambda e: self._render())
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", lambda e: self._on_select(self._tokens.id))

    def set_active(self, active: bool) -> None:
        self._is_active = active
        self._render()

    def _on_enter(self, event: Any) -> None:
        self._is_hovered = True
        self._render()

    def _on_leave(self, event: Any) -> None:
        self._is_hovered = False
        self._render()

    def _render(self) -> None:
        w = max(10, self.winfo_width())
        h = 52
        self.delete("all")

        # Fondo con esquinas redondeadas
        if self._is_active:
            fill_col = "#1b2128"
            outline_col = self._tokens.primary
            border_w = 2
        elif self._is_hovered:
            fill_col = "#1a1c24"
            outline_col = "#333748"
            border_w = 1
        else:
            fill_col = "#16171e"
            outline_col = "#252733"
            border_w = 1

        _draw_rounded_polygon(
            self,
            2,
            2,
            w - 2,
            h - 2,
            radius=8,
            fill=fill_col,
            outline=outline_col,
            width=border_w
        )

        # Muestra circular de color con halo
        self.create_oval(14, 15, 36, 37, fill=self._tokens.primary, outline="#ffffff" if self._is_active else "")

        # Nombre del tema
        self.create_text(
            48,
            20,
            text=self._tokens.name,
            anchor="w",
            fill="#ffffff" if self._is_active else "#ededed",
            font=("Segoe UI", 9, "bold" if self._is_active else "normal")
        )

        # Código Hex y Badge de Contraste WCAG 2.2
        ratio_str = f"WCAG 2.2 {self._tokens.wcag_compliance} • {self._tokens.contrast_ratio_on_dark}:1"
        self.create_text(
            48,
            36,
            text=f"{self._tokens.primary.upper()}  |  {ratio_str}",
            anchor="w",
            fill="#8b8d98",
            font=("Segoe UI", 8)
        )

        # Indicador de selección activa a la derecha
        if self._is_active:
            self.create_text(
                w - 20,
                26,
                text="✓ Activo",
                anchor="e",
                fill=self._tokens.primary,
                font=("Segoe UI", 9, "bold")
            )


class ThemeModal(tk.Toplevel):
    """Ventana flotante modal para selección y personalización de temas."""

    def __init__(
        self,
        parent: tk.Tk,
        theme_manager: ThemeManager,
        current_config: AppConfig,
        config_path: str = "config.toml"
    ) -> None:
        super().__init__(parent)
        self.title("Personalización de Colores AutoRod")
        self.geometry("440x510")
        self.resizable(False, False)
        self.configure(bg="#0c0d10")
        self.transient(parent)
        self.grab_set()

        self._theme_mgr = theme_manager
        self._config = current_config
        self._config_path = config_path

        # Centrar sobre la ventana padre
        self.update_idletasks()
        px = parent.winfo_x() + (parent.winfo_width() // 2) - 220
        py = parent.winfo_y() + (parent.winfo_height() // 2) - 255
        self.geometry(f"+{max(0, px)}+{max(0, py)}")

        self._cards: dict[str, ThemeOptionCard] = {}
        self._build_ui()

    def _build_ui(self) -> None:
        container = tk.Frame(self, bg="#0c0d10", padx=18, pady=16)
        container.pack(fill=tk.BOTH, expand=True)

        # Cabecera
        tk.Label(
            container,
            text="🎨 Personalización de Colores de la UI",
            font=("Segoe UI", 12, "bold"),
            bg="#0c0d10",
            fg="#ffffff"
        ).pack(anchor="w", pady=(0, 4))

        tk.Label(
            container,
            text="Selecciona uno de los esquemas aprobados con contraste WCAG 2.2:",
            font=("Segoe UI", 8),
            bg="#0c0d10",
            fg="#94a3b8"
        ).pack(anchor="w", pady=(0, 14))

        # Lista de temas disponibles
        for tokens in self._theme_mgr.get_all_themes():
            is_active = (tokens.id == self._theme_mgr.current_id)
            card = ThemeOptionCard(
                container,
                tokens=tokens,
                is_active=is_active,
                on_select=self._on_theme_chosen
            )
            card.pack(fill=tk.X, pady=4)
            self._cards[tokens.id] = card

        # Botón Cerrar en la parte inferior
        close_btn = tk.Button(
            container,
            text="Listo / Cerrar",
            command=self.destroy,
            bg="#1f2129",
            fg="#ffffff",
            activebackground="#2b2e3a",
            activeforeground="#ffffff",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            bd=0,
            pady=6,
            cursor="hand2"
        )
        close_btn.pack(fill=tk.X, side=tk.BOTTOM, pady=(12, 0))

    def _on_theme_chosen(self, theme_id: str) -> None:
        """Aplica el tema seleccionado y lo persiste en disco."""
        if self._theme_mgr.set_theme(theme_id):
            # Actualizar tarjetas visuales en el diálogo
            for tid, card in self._cards.items():
                card.set_active(tid == theme_id)

            # Persistir en config.toml
            try:
                updated_config = AppConfig(
                    target_fps=self._config.target_fps,
                    input_backend=self._config.input_backend,
                    vision_strategy=self._config.vision_strategy,
                    capture_source=self._config.capture_source,
                    monitor_index=self._config.monitor_index,
                    button_threshold=self._config.button_threshold,
                    cache_button_size=self._config.cache_button_size,
                    humanized_input=self._config.humanized_input,
                    ui_theme=theme_id,
                    ui_transparency=self._config.ui_transparency
                )
                save_config(updated_config, self._config_path)
            except Exception:
                pass
