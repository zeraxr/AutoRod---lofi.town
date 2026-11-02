"""Pruebas unitarias para los componentes y arquitectura de UI basada en Flet (Figma 1:1 Oficial)."""

import unittest
from autorod.infrastructure.ui.flet.theme import (
    ThemeManager,
    THEME_PRESETS,
    FIGMA_ACCENT_COLORS,
    ThemeTokens,
    calculate_contrast_ratio
)
from autorod.infrastructure.ui.flet.components.kinetic_button import (
    FletKineticGlowButton,
    FletKineticEmergencyButton
)
from autorod.infrastructure.ui.flet.components.gooey_sidebar import FletCollapsibleGooeySidebar
from autorod.infrastructure.ui.flet.components.theme_studio_view import FletThemeStudioView
from autorod.infrastructure.ui.flet.components.metric_card import FletMetricCard
from autorod.infrastructure.ui.flet.components.telemetry_view import FletTelemetryView
from autorod.infrastructure.ui.flet.components.viewport_view import FletDiagnosticsViewport
from autorod.infrastructure.ui.flet.components.skeleton_view import FletDashboardSkeleton
from autorod.infrastructure.ui.flet.components.title_bar import FletCustomTitleBar
from autorod.infrastructure.ui.flet.components.settings_view import FletSettingsView
from autorod.infrastructure.ui.flet.components.parameters_view import FletParametersView
from autorod.infrastructure.ui.flet.components.help_view import FletHelpView
from autorod.infrastructure.updater.github_checker import UpdateInfo
from autorod.infrastructure.ui.flet.utils import (
    safe_update,
    get_control_page,
    is_control_mounted,
    close_app_window
)
import flet as ft
from autorod.config import AppConfig


class TestFletUIArchitecture(unittest.TestCase):
    def setUp(self) -> None:
        self.theme_mgr = ThemeManager("default")

    def test_figma_theme_tokens_and_wcag_contrast(self) -> None:
        """Verifica que los modos base Oscuro y Claro y los 6 acentos cumplan WCAG 2.2."""
        self.assertEqual(len(FIGMA_ACCENT_COLORS), 6)
        accent_hexes = [a[0] for a in FIGMA_ACCENT_COLORS]
        self.assertIn("#5554d9", accent_hexes)

        # Verificar contraste de tokens oscuros y claros
        dark_tokens = self.theme_mgr.current
        self.assertEqual(dark_tokens.shell_bg, "#1a1b26")
        self.assertEqual(dark_tokens.canvas_bg, "#11151f")
        self.assertEqual(dark_tokens.card_bg, "#0d0f17")

        self.theme_mgr.set_theme_mode("light")
        light_tokens = self.theme_mgr.current
        self.assertEqual(light_tokens.shell_bg, "#dadde9")
        self.assertEqual(light_tokens.canvas_bg, "#f2f3f8")
        self.assertEqual(light_tokens.card_bg, "#ffffff")

        # Restaurar
        self.theme_mgr.set_theme_mode("dark")

    def test_kinetic_glow_button_initialization(self) -> None:
        """Verifica la inicialización del botón cinético Flet."""
        clicked = False
        def _on_click() -> None:
            nonlocal clicked
            clicked = True

        btn = FletKineticGlowButton(
            text="TEST BUTTON",
            on_click=_on_click,
            is_primary=True,
            theme_manager=self.theme_mgr
        )
        self.assertEqual(btn._btn_text.value, "TEST BUTTON")
        self.assertEqual(btn.scale, 1.0)
        btn._handle_click(None)
        self.assertTrue(clicked)
        self.assertEqual(btn._btn_text.value, "EJECUTADO")

    def test_emergency_button_bounds_prevent_clipping(self) -> None:
        """Verifica que el botón de emergencia en Flet tenga medidas seguras contra recorte."""
        btn = FletKineticEmergencyButton(
            on_click=lambda: None,
            text="SALIR [Alt+Q]",
            width=130,
            height=36
        )
        self.assertEqual(btn._text_ctrl.value, "SALIR [Alt+Q]")
        self.assertGreaterEqual(btn.width, 120)
        self.assertEqual(btn.height, 36)

    def test_collapsible_sidebar_all_six_tabs(self) -> None:
        """Verifica que la barra lateral tenga las 6 pestañas oficiales de Figma y colapse."""
        selected_tab = None
        def _on_select(t: str) -> None:
            nonlocal selected_tab
            selected_tab = t

        sidebar = FletCollapsibleGooeySidebar(
            on_tab_selected=_on_select,
            theme_manager=self.theme_mgr
        )

        tab_ids = [t[0] for t in sidebar.TAB_ITEMS]
        self.assertEqual(tab_ids, ["dashboard", "settings", "palette", "telemetry", "parameters", "help"])
        self.assertEqual(sidebar.width, 220)

        # Alternar colapso (220 -> 72 -> 220)
        sidebar.toggle_collapsed()
        self.assertEqual(sidebar.width, 72)
        sidebar.toggle_collapsed()
        self.assertEqual(sidebar.width, 220)

        # Seleccionar pestañas
        sidebar.select_tab("parameters")
        self.assertEqual(selected_tab, "parameters")
        sidebar.select_tab("help")
        self.assertEqual(selected_tab, "help")

    def test_theme_studio_view_in_window(self) -> None:
        """Verifica que el estudio de diseño monte los 3 modos de tema y los 6 swatches oficiales."""
        cfg = AppConfig()
        view = FletThemeStudioView(
            theme_manager=self.theme_mgr,
            config=cfg
        )
        self.assertEqual(len(view._theme_cards), 3)
        self.assertIn("dark", view._theme_cards)
        self.assertIn("light", view._theme_cards)
        self.assertIn("system", view._theme_cards)

        self.assertEqual(len(view._swatch_containers), 6)

        # Probar selección de modo claro
        view._on_mode_select("light")
        self.assertEqual(self.theme_mgr.mode, "light")

        # Probar selección de swatch
        view._on_accent_select("#7dcfff")
        self.assertEqual(self.theme_mgr.accent, "#7dcfff")

    def test_metric_card_updates(self) -> None:
        """Verifica actualización de tarjetas métricas."""
        card = FletMetricCard(
            title="LATENCIA",
            default_val="20 ms",
            subtext="FPS 60",
            theme_manager=self.theme_mgr
        )
        self.assertEqual(card._val_text.value, "20 ms")
        card.update_val("15 ms", color="#38bdf8", sub="FPS 60 estable")
        self.assertEqual(card._val_text.value, "15 ms")
        self.assertEqual(card._sub_text.value, "FPS 60 estable")

    def test_telemetry_view_append_log_unmounted_does_not_raise(self) -> None:
        """Verifica que instanciar y agregar logs a FletTelemetryView fuera de página sea seguro."""
        tv = FletTelemetryView(theme_manager=self.theme_mgr)
        self.assertGreaterEqual(len(tv._log_column.controls), 2)
        tv.append_log("Prueba de logging no montado")
        self.assertIn("Prueba de logging no montado", tv._log_column.controls[-1].value)

    def test_viewport_update_image_unmounted_does_not_raise(self) -> None:
        """Verifica que actualizar la imagen en FletDiagnosticsViewport no montado sea seguro."""
        vp = FletDiagnosticsViewport(theme_manager=self.theme_mgr)
        vp.update_image(b"fake_png_bytes")
        self.assertEqual(vp.image_control.src, b"fake_png_bytes")

    def test_utils_safe_update_and_get_control_page(self) -> None:
        """Verifica que get_control_page y safe_update manejen controles no montados sin error."""
        c = ft.Container()
        self.assertIsNone(get_control_page(c))
        self.assertFalse(is_control_mounted(c))
        safe_update(c)
        safe_update(None)

    def test_custom_title_bar_name_omits_v2_and_handles_updates(self) -> None:
        """Verifica que la barra personalizada muestre 'AutoRod' sin 'v2.0' y gestione el botón de update."""
        closed = False
        def _on_close() -> None:
            nonlocal closed
            closed = True

        tb = FletCustomTitleBar(
            page=None,
            on_close=_on_close,
            theme_manager=self.theme_mgr
        )
        self.assertEqual(tb._title_text.value, "AutoRod")
        self.assertNotIn("v2.0", tb._title_text.value)
        self.assertFalse(tb._update_button.visible)

        info = UpdateInfo(
            has_update=True,
            latest_version="v2.1.0",
            current_version="2.0.0",
            release_name="AutoRod v2.1.0",
            release_notes="Notas de prueba",
            html_url="https://github.com/zeraxr/AutoRod",
            download_url="https://github.com/zeraxr/AutoRod"
        )
        tb.set_update_available(info)
        self.assertTrue(tb._update_button.visible)
        self.assertIn("v2.1.0", tb._update_btn_text.value)

        tb._on_close()
        self.assertTrue(closed)

    def test_close_app_window_handles_none_gracefully(self) -> None:
        """Verifica que close_app_window con None o sin ventana no lance excepciones."""
        close_app_window(None)

    def test_skeleton_view_initialization_and_theme_update(self) -> None:
        """Verifica que FletDashboardSkeleton cree la geometría de carga y responda a temas."""
        skeleton = FletDashboardSkeleton(theme_manager=self.theme_mgr)
        self.assertEqual(len(skeleton._metric_skeletons), 4)
        self.assertIsNotNone(skeleton._spinner)
        self.theme_mgr.set_theme("purple")
        self.assertEqual(skeleton._spinner.color, self.theme_mgr.current.primary)

    def test_collapsible_sidebar_liquid_indicator_and_shortcuts(self) -> None:
        """Verifica los atajos, el indicador líquido y el estado de la barra lateral."""
        selected = None
        def _cb(t: str) -> None:
            nonlocal selected
            selected = t

        sidebar = FletCollapsibleGooeySidebar(on_tab_selected=_cb, theme_manager=self.theme_mgr)
        self.assertEqual(len(sidebar._tab_indicators), 6)
        self.assertEqual(sidebar._tab_indicators["dashboard"].bgcolor, self.theme_mgr.current.primary)

        sidebar.select_tab("settings")
        self.assertEqual(selected, "settings")
        self.assertEqual(sidebar._tab_indicators["settings"].bgcolor, self.theme_mgr.current.primary)
        self.assertEqual(sidebar._tab_indicators["dashboard"].bgcolor, ft.Colors.TRANSPARENT)

    def test_sober_look_and_zero_emojis_in_flet_ui(self) -> None:
        """Verifica que no existan sombras/glows y que la UI esté 100% libre de emojis."""
        import re
        emoji_pattern = re.compile(r'[\U00010000-\U0010ffff\u2600-\u27bf\u2300-\u23ff\u2b50]')

        # 1. Botón cinético sobrio sin BoxShadow
        btn = FletKineticGlowButton(
            text="BOTON TEST",
            on_click=lambda: None,
            icon=ft.Icons.CHECK_ROUNDED,
            theme_manager=self.theme_mgr
        )
        self.assertIsNone(btn.shadow)

        # 2. ThemeStudioView sin emojis
        studio = FletThemeStudioView(theme_manager=self.theme_mgr, config=AppConfig())
        self.assertFalse(bool(emoji_pattern.findall(studio._title_text.value)))
        self.assertFalse(bool(emoji_pattern.findall(studio._subtitle_text.value)))

        # 3. Settings View sin emojis
        settings = FletSettingsView(config=AppConfig(), theme_manager=self.theme_mgr)
        self.assertFalse(bool(emoji_pattern.findall(settings._title_text.value)))
        for opt in settings._fps_dropdown.options:
            self.assertFalse(bool(emoji_pattern.findall(opt.text)))

        # 4. Parameters View sin emojis
        params = FletParametersView(config=AppConfig(), theme_manager=self.theme_mgr)
        self.assertFalse(bool(emoji_pattern.findall(params._title_text.value)))
        for opt in params._profile_dropdown.options:
            self.assertFalse(bool(emoji_pattern.findall(opt.text)))

        # 5. Help View sin emojis
        help_v = FletHelpView(theme_manager=self.theme_mgr)
        self.assertFalse(bool(emoji_pattern.findall(help_v._title_text.value)))

    def test_parameters_view_initialization_and_saving(self) -> None:
        """Verifica el panel de Parámetros oficial de Figma y su serialización."""
        cfg = AppConfig(min_confidence=0.88, color_tolerance=0.18, cast_delay_ms=1600)
        saved_cfg = None
        def _on_save(c: AppConfig) -> None:
            nonlocal saved_cfg
            saved_cfg = c

        params = FletParametersView(
            config=cfg,
            on_save_callback=_on_save,
            theme_manager=self.theme_mgr
        )
        self.assertEqual(params._conf_slider.value, 88)
        self.assertEqual(params._color_tol_slider.value, 18)
        self.assertEqual(params._cast_delay_slider.value, 1600)

        # Guardar cambios
        params._conf_slider.value = 90
        params._on_save_click(None)
        self.assertIsNotNone(saved_cfg)
        self.assertEqual(saved_cfg.min_confidence, 0.90)

    def test_help_view_initialization_and_search(self) -> None:
        """Verifica la vista de Ayuda con buscador en tiempo real y pasos."""
        help_v = FletHelpView(theme_manager=self.theme_mgr)
        self.assertEqual(len(help_v._faq_data), 4)

        # Buscar término que solo coincide con una pregunta
        help_v._search_input.value = "cambiar de ventana"
        help_v._on_search_query(None)
        visible_faqs = [c for c in help_v._faq_containers if c.visible]
        self.assertEqual(len(visible_faqs), 1)

    def test_minimalist_topbar_breadcrumbs_all_views(self) -> None:
        """Verifica que el título superior sea limpio en las 6 pestañas de Figma."""
        from autorod.infrastructure.ui.flet.app import FletMainApp
        from unittest.mock import MagicMock
        app = FletMainApp(
            runner=MagicMock(),
            diagnostics=MagicMock(),
            renderer=MagicMock(),
            config=AppConfig()
        )
        app._breadcrumb_text = ft.Text("Inicio")
        for tab in ("dashboard", "settings", "palette", "telemetry", "parameters", "help"):
            app._current_tab = tab
            app._update_breadcrumb_text()
            val = app._breadcrumb_text.value
            self.assertNotIn("AutoRod", val)
            self.assertNotIn("Paleta:", val)
        self.assertEqual(app._breadcrumb_text.value, "Ayuda")

    def test_time_based_greeting_and_splash_phrases(self) -> None:
        """Verifica los saludos dinámicos según hora local y las frases motivacionales/estilo Minecraft."""
        from datetime import datetime
        from autorod.infrastructure.ui.flet.components.viewport_view import (
            get_time_based_greeting,
            MINECRAFT_SPLASH_PHRASES,
            get_random_splash_phrase,
        )

        morning_dt = datetime(2026, 11, 2, 8, 30)
        afternoon_dt = datetime(2026, 11, 2, 15, 0)
        evening_dt = datetime(2026, 11, 2, 22, 15)

        self.assertEqual(get_time_based_greeting(morning_dt), "¡Buenos días!")
        self.assertEqual(get_time_based_greeting(afternoon_dt), "¡Buenas tardes!")
        self.assertEqual(get_time_based_greeting(evening_dt), "¡Buenas noches!")

        user_expected_phrases = [
            "¡Procura beber agua! :)",
            "¡Eres importante, nunca lo olvides!",
            "¡Otro día de pesca, otro día de farmeo! :3",
            "El omega 3!! El omega 3!!!! D::::",
            "¡No bajes los brazos! Mucho ánimo!!",
        ]
        for phrase in user_expected_phrases:
            self.assertIn(phrase, MINECRAFT_SPLASH_PHRASES)

        vp = FletDiagnosticsViewport(theme_manager=self.theme_mgr)
        self.assertIn(vp._greeting_text.value, ("¡Buenos días!", "¡Buenas tardes!", "¡Buenas noches!"))
        self.assertIn(vp._splash_text.value, MINECRAFT_SPLASH_PHRASES)

    def test_unified_category_styles_action_button_theming_and_checklist(self) -> None:
        """
        Verifica:
        1. Rediseño unificado de todas las categorías con el estilo Inicio (#11151f).
        2. Personalización cromática que afecta exclusivamente el contorno de 'pausar' y relleno de 'iniciar'.
        3. Apartado de Rendimiento y Apariencia con checklist: 'saludos', 'hora local', 'animaciones de transición'.
        """
        cfg = AppConfig(
            show_greetings=True,
            use_local_time=True,
            enable_transition_animations=True
        )

        vp = FletDiagnosticsViewport(theme_manager=self.theme_mgr, config=cfg)
        studio = FletThemeStudioView(theme_manager=self.theme_mgr, config=cfg)
        telemetry = FletTelemetryView(theme_manager=self.theme_mgr)
        settings = FletSettingsView(config=cfg, theme_manager=self.theme_mgr)
        parameters = FletParametersView(config=cfg, theme_manager=self.theme_mgr)
        help_v = FletHelpView(theme_manager=self.theme_mgr)

        for view in (vp, studio, telemetry, settings, parameters, help_v):
            self.assertEqual(view.bgcolor, "#11151f")
            self.assertIsNotNone(view.border_radius)
            self.assertEqual(view.border_radius.top_left, 16)
            self.assertEqual(view.border_radius.bottom_left, 16)

        # Verificación de checklist
        self.assertEqual(studio._chk_saludos.label, "saludos")
        self.assertEqual(studio._chk_hora_local.label, "hora local")
        self.assertEqual(studio._chk_animaciones.label, "animaciones de transición")

        # Personalización cromática exclusiva de contorno pausar y relleno iniciar
        vp.apply_button_theme("#06b6d4")
        self.assertEqual(vp._quick_pause_btn.border.left.color, "#06b6d4")
        self.assertEqual(vp._quick_play_btn.bgcolor, "#06b6d4")
        self.assertEqual(vp._quick_pause_btn.bgcolor, "#141a2a")


if __name__ == "__main__":
    unittest.main()
