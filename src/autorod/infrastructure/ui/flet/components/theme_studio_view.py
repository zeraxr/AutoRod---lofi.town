"""Vista de Estudio de Personalización Visual en Flet (Single Window)."""

from typing import Callable, Any
import flet as ft
from autorod.infrastructure.ui.flet.theme import ThemeManager, ThemeTokens
from autorod.config import AppConfig, save_config
from autorod.infrastructure.ui.flet.components.kinetic_button import FletKineticGlowButton
from autorod.infrastructure.ui.flet.components.metric_card import FletMetricCard
from autorod.infrastructure.ui.flet.window_fx import FletWindowFX
from autorod.infrastructure.ui.flet.utils import safe_update, get_control_page


class FletThemeOptionCard(ft.Container):
    """Tarjeta de opción de tema en Flet con muestra de color, contraste y badge WCAG."""

    def __init__(
        self,
        tokens: ThemeTokens,
        is_active: bool,
        on_select: Callable[[str], None]
    ) -> None:
        self._tokens = tokens
        self._is_active = is_active
        self._on_select = on_select

        self._swatch = ft.Container(
            width=26,
            height=26,
            border_radius=13,
            bgcolor=tokens.primary,
            border=ft.Border.all(2, "#ffffff" if is_active else tokens.primary),
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=8, color=tokens.glow_color) if is_active else None
        )

        self._name_text = ft.Text(tokens.name, size=13, weight=ft.FontWeight.BOLD, color="#ffffff")
        self._hex_text = ft.Text(tokens.primary.upper(), size=11, color="#9ca3af", font_family="Consolas")
        self._wcag_badge = ft.Container(
            content=ft.Text(f"WCAG {tokens.wcag_compliance} • {tokens.contrast_ratio_on_dark}:1", size=10, weight=ft.FontWeight.BOLD, color=tokens.badge_fg),
            bgcolor=tokens.badge_bg,
            border_radius=6,
            padding=ft.Padding.symmetric(horizontal=8, vertical=3)
        )
        self._status_badge = ft.Container(
            content=ft.Text(
                "✓ ACTIVO" if is_active else "Seleccionar",
                size=11,
                weight=ft.FontWeight.BOLD,
                color=tokens.primary if is_active else "#64748b"
            ),
            padding=ft.Padding.symmetric(horizontal=8, vertical=2),
            border_radius=6,
            bgcolor=tokens.accent_subtle if is_active else ft.Colors.TRANSPARENT
        )

        super().__init__(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Row(controls=[self._swatch, self._name_text], spacing=10),
                            self._status_badge
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                    ),
                    ft.Row(
                        controls=[
                            self._hex_text,
                            self._wcag_badge
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                    )
                ],
                spacing=10
            ),
            bgcolor="#151824" if is_active else "#11131c",
            border=ft.Border.all(1.5 if is_active else 1, tokens.primary if is_active else "#1f2334"),
            border_radius=12,
            padding=ft.Padding.all(14),
            on_click=lambda e: self._on_select(self._tokens.id),
            animate=ft.Animation(180, ft.AnimationCurve.EASE_OUT),
            ink=True
        )

    def set_active(self, active: bool) -> None:
        self._is_active = active
        self.bgcolor = "#151824" if active else "#11131c"
        self.border = ft.Border.all(1.5 if active else 1, self._tokens.primary if active else "#1f2334")
        self._swatch.border = ft.Border.all(2, "#ffffff" if active else self._tokens.primary)
        self._swatch.shadow = ft.BoxShadow(spread_radius=1, blur_radius=8, color=self._tokens.glow_color) if active else None
        self._status_badge.content.value = "✓ ACTIVO" if active else "Seleccionar"
        self._status_badge.content.color = self._tokens.primary if active else "#64748b"
        self._status_badge.bgcolor = self._tokens.accent_subtle if active else ft.Colors.TRANSPARENT
        safe_update(self)


class FletThemeStudioView(ft.Container):
    """Vista de personalización visual completa integrada en la misma ventana."""

    def __init__(
        self,
        theme_manager: ThemeManager,
        config: AppConfig,
        config_path: str = "config.toml"
    ) -> None:
        self._theme_mgr = theme_manager
        self._config = config
        self._config_path = config_path

        self._cards: dict[str, FletThemeOptionCard] = {}

        self._reset_btn = FletKineticGlowButton(
            text="↺ RESTABLECER POR DEFECTO",
            on_click=self._reset_to_default_theme,
            width=210,
            height=36,
            is_primary=False,
            confirmed_text="✓ RESTAURADO",
            theme_manager=self._theme_mgr
        )

        header = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Column(
                        controls=[
                            ft.Text("🎨 Estudio de Personalización y Diseño Visual", size=18, weight=ft.FontWeight.BOLD, color="#ffffff"),
                            ft.Text("Configura la atmósfera cromática y translucidez de AutoRod en tiempo real. 100% integrado dentro del mismo programa.", size=12, color="#9ca3af")
                        ],
                        spacing=3,
                        expand=True
                    ),
                    self._reset_btn
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER
            ),
            bgcolor="#11131c",
            border=ft.Border.all(1, "#1e2232"),
            border_radius=10,
            padding=ft.Padding.symmetric(horizontal=16, vertical=12)
        )

        row1 = ft.Row(spacing=10, expand=True)
        row2 = ft.Row(spacing=10, expand=True)

        all_themes = self._theme_mgr.get_all_themes()
        for idx, tokens in enumerate(all_themes):
            card = FletThemeOptionCard(
                tokens=tokens,
                is_active=(tokens.id == self._theme_mgr.current_id),
                on_select=self._on_theme_chosen
            )
            card.expand = True
            self._cards[tokens.id] = card
            if idx < 3:
                row1.controls.append(card)
            else:
                row2.controls.append(card)

        self._sample_btn = FletKineticGlowButton(
            text="PROBAR BOTÓN",
            on_click=lambda: None,
            width=150,
            is_primary=True,
            confirmed_text="✓ FUNCIONA",
            theme_manager=self._theme_mgr
        )
        self._sample_metric = FletMetricCard(
            title="MUESTRA EN VIVO",
            default_val="100% OK",
            subtext="Tema sincronizado",
            theme_manager=self._theme_mgr
        )

        self._opacity_slider = ft.Slider(
            min=0.60,
            max=1.00,
            divisions=20,
            value=self._config.ui_transparency,
            label="{value}",
            on_change=self._on_opacity_changed,
            expand=True
        )

        sandbox_panel = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("Vista Previa en Vivo & Opacidad de Ventana", size=13, weight=ft.FontWeight.BOLD, color="#ffffff"),
                    ft.Row(
                        controls=[
                            ft.Container(content=self._sample_btn, width=160),
                            ft.Container(content=self._sample_metric, width=200),
                            ft.Container(
                                content=ft.Column(
                                    controls=[
                                        ft.Text("Opacidad de Ventana (Fusión con software de fondo):", size=11, color="#9ca3af"),
                                        self._opacity_slider
                                    ],
                                    spacing=4
                                ),
                                expand=True
                            )
                        ],
                        spacing=16,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER
                    )
                ],
                spacing=10
            ),
            bgcolor="#11131c",
            border=ft.Border.all(1, "#1e2232"),
            border_radius=10,
            padding=ft.Padding.symmetric(horizontal=16, vertical=14)
        )

        self._toast_text = ft.Text("", size=12, weight=ft.FontWeight.BOLD, color=self._theme_mgr.current.primary)

        super().__init__(
            content=ft.Column(
                controls=[
                    header,
                    row1,
                    row2,
                    sandbox_panel,
                    self._toast_text
                ],
                spacing=12,
                scroll=ft.ScrollMode.ADAPTIVE
            ),
            expand=True,
            padding=ft.Padding.all(14)
        )

    def _reset_to_default_theme(self) -> None:
        """Restaura la paleta 'default' (Supabase Emerald) y la opacidad predeterminada."""
        default_theme = "default"
        default_opacity = 0.96

        self._opacity_slider.value = default_opacity
        page = get_control_page(self)
        if page:
            try:
                FletWindowFX.apply_transparency(page, default_opacity)
            except Exception:
                pass

        self._on_theme_chosen(default_theme)
        self._toast_text.value = "✓ Tema restaurado a la configuración por defecto (Supabase Emerald • 96% Opacidad)."
        self._toast_text.color = self._theme_mgr.current.primary
        safe_update(self)

    def _on_theme_chosen(self, theme_id: str) -> None:
        if self._theme_mgr.set_theme(theme_id):
            for tid, card in self._cards.items():
                card.set_active(tid == theme_id)

            self._toast_text.value = f"✓ Paleta '{self._theme_mgr.current.name}' aplicada con éxito en todo el sistema."
            self._toast_text.color = self._theme_mgr.current.primary

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
                    ui_transparency=self._opacity_slider.value
                )
                self._config = updated_config
                save_config(updated_config, self._config_path)
            except Exception:
                pass

            safe_update(self)

    def _on_opacity_changed(self, e: Any) -> None:
        val = round(float(e.control.value), 2)
        page = get_control_page(self)
        if page:
            try:
                FletWindowFX.apply_transparency(page, val)
            except Exception:
                pass

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
                ui_theme=self._theme_mgr.current_id,
                ui_transparency=val
            )
            self._config = updated_config
            save_config(updated_config, self._config_path)
        except Exception:
            pass
