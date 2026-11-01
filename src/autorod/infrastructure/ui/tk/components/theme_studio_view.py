"""Vista Integrada de Personalización Visual y Estudio de Temas para AutoRod.

Permite gestionar la atmósfera visual y paletas 100% dentro de la ventana principal,
eliminando ventanas emergentes innecesarias (Toplevel).

Incluye:
- Selector en cuadrícula de las 6 paletas aprobadas WCAG 2.2:
  1. Por defecto (Supabase Emerald #3ECF8E)
  2. Blanco (Minimalista #FFFFFF)
  3. Rojo (Cyberpunk #EF4444)
  4. Verde GitHub (Primer #2EA043)
  5. Morado (Neon Violet #8B5CF6)
  6. Celeste (Electric Sky #38BDF8)
- Tarjetas cinéticas interactivas con halo de color y badge de ratio de contraste.
- Sandbox interactivo en vivo con botón cinético y tarjeta de telemetría de muestra.
- Control deslizante en tiempo real de translucidez de ventana (Acrylic / Opacidad).
- Persistencia automática en config.toml.
"""

import tkinter as tk
from typing import Callable, Any
from autorod.infrastructure.ui.tk.theme import ThemeManager, ThemeTokens, THEME_PRESETS
from autorod.config import AppConfig, save_config
from autorod.infrastructure.ui.tk.components.glow_button import (
    KineticGlowButton,
    _draw_rounded_polygon,
    _blend_color
)
from autorod.infrastructure.ui.tk.window_fx import WindowFXManager


class ThemeStudioCard(tk.Canvas):
    """Tarjeta interactiva de selección de tema con muestra de color, halo y ratio WCAG."""

    def __init__(
        self,
        parent: tk.Widget,
        tokens: ThemeTokens,
        is_active: bool,
        on_select: Callable[[str], None]
    ) -> None:
        super().__init__(
            parent,
            height=100,
            bg=parent.cget("bg"),
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
        if not self.winfo_exists():
            return
        w = max(10, self.winfo_width())
        h = 100
        self.delete("all")

        # Color de fondo y borde según estado
        if self._is_active:
            bg_fill = "#181b28"
            border_col = self._tokens.primary
            border_w = 2
        elif self._is_hovered:
            bg_fill = "#151722"
            border_col = "#383d54"
            border_w = 1
        else:
            bg_fill = "#11131c"
            border_col = "#202334"
            border_w = 1

        # Resplandor exterior si está activo o con hover
        if self._is_active:
            glow_col = _blend_color("#090a0f", self._tokens.glow_color, 0.22, self)
            _draw_rounded_polygon(
                self,
                1,
                1,
                w - 1,
                h - 1,
                radius=14,
                fill=glow_col,
                outline="",
                tags="glow"
            )

        # Superficie de la tarjeta
        _draw_rounded_polygon(
            self,
            3,
            3,
            w - 3,
            h - 3,
            radius=12,
            fill=bg_fill,
            outline=border_col,
            width=border_w,
            tags="card_surface"
        )

        # Brillo superior
        sheen = _blend_color(border_col, "#ffffff", 0.35, self)
        self.create_line(16, 4, w - 16, 4, fill=sheen, width=1)

        # Círculo de muestra de color con halo interior
        cx, cy, cr = 34, 38, 16
        # Halo circular exterior
        self.create_oval(cx - cr - 3, cy - cr - 3, cx + cr + 3, cy + cr + 3,
                          fill=_blend_color(bg_fill, self._tokens.primary, 0.3, self), outline="")
        # Círculo sólido
        self.create_oval(cx - cr, cy - cr, cx + cr, cy + cr,
                          fill=self._tokens.primary, outline="#ffffff" if self._is_active else "")

        # Nombre del tema
        self.create_text(
            64,
            30,
            text=self._tokens.name,
            anchor="w",
            fill="#ffffff",
            font=("Segoe UI", 10, "bold")
        )

        # Código Hex
        self.create_text(
            64,
            48,
            text=self._tokens.primary.upper(),
            anchor="w",
            fill="#94a3b8",
            font=("Consolas", 9)
        )

        # Badge WCAG 2.2
        ratio_str = f"WCAG 2.2 {self._tokens.wcag_compliance} • {self._tokens.contrast_ratio_on_dark}:1"
        badge_bg = self._tokens.badge_bg
        badge_fg = self._tokens.badge_fg
        
        _draw_rounded_polygon(
            self,
            16,
            68,
            168,
            88,
            radius=6,
            fill=badge_bg,
            outline="",
            tags="badge"
        )
        self.create_text(
            92,
            78,
            text=ratio_str,
            fill=badge_fg,
            font=("Segoe UI", 8, "bold")
        )

        # Píldora de Selección a la derecha
        if self._is_active:
            _draw_rounded_polygon(
                self,
                w - 100,
                68,
                w - 16,
                88,
                radius=6,
                fill=self._tokens.primary,
                outline="",
                tags="sel_badge"
            )
            self.create_text(
                w - 58,
                78,
                text="✓ ACTIVO",
                fill=self._tokens.text_on_primary,
                font=("Segoe UI", 8, "bold")
            )
        else:
            self.create_text(
                w - 30,
                78,
                text="Elegir ➔",
                anchor="e",
                fill="#64748b" if not self._is_hovered else "#94a3b8",
                font=("Segoe UI", 8, "bold")
            )


class ThemeStudioView(tk.Frame):
    """Panel de estudio de diseño integrado dentro del mismo programa principal."""

    def __init__(
        self,
        parent: tk.Widget,
        theme_manager: ThemeManager,
        app_config: AppConfig,
        config_path: str = "config.toml",
        on_transparency_changed: Callable[[float], None] | None = None
    ) -> None:
        super().__init__(parent, bg="#090a0f")
        self._theme_mgr = theme_manager
        self._config = app_config
        self._config_path = config_path
        self._on_transp_changed = on_transparency_changed

        self._cards: dict[str, ThemeStudioCard] = {}
        self._build_studio()

    def _build_studio(self) -> None:
        # Contenedor con scroll suave o layout fluido
        main_box = tk.Frame(self, bg="#090a0f")
        main_box.pack(fill=tk.BOTH, expand=True, padx=12, pady=8)

        # 1. Cabecera del Estudio
        header_card = tk.Frame(main_box, bg="#11131c", padx=18, pady=14)
        header_card.pack(fill=tk.X, pady=(0, 12))

        tk.Label(
            header_card,
            text="🎨 Estudio de Personalización y Diseño Visual",
            font=("Segoe UI", 13, "bold"),
            bg="#11131c",
            fg="#ffffff"
        ).pack(anchor="w", pady=(0, 2))

        tk.Label(
            header_card,
            text="Configura la paleta de color y translucidez de AutoRod en tiempo real. Todos los componentes se actualizan instantáneamente sin reiniciar.",
            font=("Segoe UI", 9),
            bg="#11131c",
            fg="#94a3b8"
        ).pack(anchor="w")

        # 2. Grid de las 6 Paletas de Color
        grid_frame = tk.Frame(main_box, bg="#090a0f")
        grid_frame.pack(fill=tk.X, pady=(0, 12))
        grid_frame.columnconfigure(0, weight=1, uniform="theme_cols")
        grid_frame.columnconfigure(1, weight=1, uniform="theme_cols")
        grid_frame.columnconfigure(2, weight=1, uniform="theme_cols")

        all_themes = self._theme_mgr.get_all_themes()
        for idx, tokens in enumerate(all_themes):
            row = idx // 3
            col = idx % 3
            is_active = (tokens.id == self._theme_mgr.current_id)
            card = ThemeStudioCard(
                grid_frame,
                tokens=tokens,
                is_active=is_active,
                on_select=self._on_select_theme
            )
            card.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
            self._cards[tokens.id] = card

        # 3. Sandbox de Prueba en Vivo (Live Preview) y Control de Transparencia
        preview_panel = tk.Frame(main_box, bg="#11131c", padx=18, pady=16)
        preview_panel.pack(fill=tk.X, pady=(0, 8))

        tk.Label(
            preview_panel,
            text="Vista Previa de Componentes Cinéticos & Translucidez de Ventana",
            font=("Segoe UI", 10, "bold"),
            bg="#11131c",
            fg="#ffffff"
        ).pack(anchor="w", pady=(0, 10))

        preview_cols = tk.Frame(preview_panel, bg="#11131c")
        preview_cols.pack(fill=tk.X)

        # Botón de demostración interactivo
        demo_box = tk.Frame(preview_cols, bg="#11131c")
        demo_box.pack(side=tk.LEFT, padx=(0, 24))

        tk.Label(
            demo_box,
            text="Botón Cinético Activo:",
            font=("Segoe UI", 8, "bold"),
            bg="#11131c",
            fg="#94a3b8"
        ).pack(anchor="w", pady=(0, 6))

        self._demo_btn = KineticGlowButton(
            demo_box,
            text="PROBAR EFECTO",
            command=lambda: None,
            width=150,
            height=34,
            is_primary=True,
            confirmed_text="✓ FUNCIONA",
            theme_manager=self._theme_mgr
        )
        self._demo_btn.pack(anchor="w")

        # Control de Transparencia / Opacidad de Ventana
        slider_box = tk.Frame(preview_cols, bg="#11131c")
        slider_box.pack(side=tk.LEFT, fill=tk.X, expand=True)

        tk.Label(
            slider_box,
            text="Opacidad de Ventana (Fusión con software y fondo de escritorio):",
            font=("Segoe UI", 8, "bold"),
            bg="#11131c",
            fg="#94a3b8"
        ).pack(anchor="w", pady=(0, 2))

        self._transp_var = tk.DoubleVar(value=self._config.ui_transparency)
        self._slider = tk.Scale(
            slider_box,
            from_=0.60,
            to=1.00,
            resolution=0.02,
            orient=tk.HORIZONTAL,
            variable=self._transp_var,
            bg="#161824",
            fg="#f1f5f9",
            highlightthickness=0,
            troughcolor="#202436",
            activebackground="#3ecf8e",
            length=260,
            command=self._on_slider_move
        )
        self._slider.pack(anchor="w")

        # Toast de estado
        self._toast_lbl = tk.Label(
            main_box,
            text="",
            font=("Segoe UI", 9, "bold"),
            bg="#090a0f",
            fg="#3ecf8e"
        )
        self._toast_lbl.pack(anchor="w", pady=(4, 0))

    def _on_select_theme(self, theme_id: str) -> None:
        """Aplica el tema seleccionado instantáneamente y lo persiste."""
        if self._theme_mgr.set_theme(theme_id):
            for tid, card in self._cards.items():
                card.set_active(tid == theme_id)

            # Actualizar color del slider
            self._slider.config(activebackground=self._theme_mgr.current.primary)

            # Persistir
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
                    ui_transparency=self._transp_var.get()
                )
                self._config = updated_config
                save_config(updated_config, self._config_path)

                self._toast_lbl.config(
                    text=f"✓ Tema '{self._theme_mgr.current.name}' aplicado con éxito en toda la aplicación.",
                    fg=self._theme_mgr.current.primary
                )
                self.after(3000, lambda: self._toast_lbl.config(text=""))
            except Exception as exc:
                self._toast_lbl.config(text=f"Error al guardar: {exc}", fg="#ef4444")

    def _on_slider_move(self, val_str: str) -> None:
        """Ajusta la transparencia de la ventana en tiempo real."""
        try:
            val = float(val_str)
            if self._on_transp_changed:
                self._on_transp_changed(val)

            updated_config = AppConfig(
                target_fps=self._config.target_fps,
                input_backend=self._config.input_backend,
                vision_strategy=self._config.vision_strategy,
                capture_source=self._config.capture_source,
                monitor_index=self._config.monitor_index,
                button_threshold=self._config.button_threshold,
                cache_button_size=self._config.cache_button_size,
                humanized_input=self._config.humanized_input,
                ui_theme=self._theme_mgr.current_id,
                ui_transparency=val
            )
            self._config = updated_config
            save_config(updated_config, self._config_path)
        except Exception:
            pass
