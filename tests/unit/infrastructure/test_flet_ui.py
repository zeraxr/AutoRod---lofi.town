"""Pruebas unitarias para los componentes y arquitectura de UI basada en Flet."""

import unittest
from autorod.infrastructure.ui.flet.theme import (
    ThemeManager,
    THEME_PRESETS,
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

    def test_all_six_themes_defined_with_wcag_compliance(self) -> None:
        """Verifica que las 6 paletas existan y cumplan WCAG 2.2 AA / AAA."""
        required = {"default", "white", "red", "github_green", "purple", "cyan"}
        self.assertTrue(required.issubset(set(THEME_PRESETS.keys())))

        dark_bg = "#090a0f"
        for tid, tokens in THEME_PRESETS.items():
            ratio = calculate_contrast_ratio(tokens.primary, dark_bg)
            self.assertGreaterEqual(
                ratio,
                4.5,
                f"El tema '{tid}' ({tokens.primary}) no cumple el ratio mínimo de 4.5:1 contra {dark_bg}"
            )
            self.assertIn(tokens.wcag_compliance, ("AA", "AAA"))

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
            text="SALIR [Q]",
            width=130,
            height=36
        )
        self.assertEqual(btn._text_ctrl.value, "SALIR [Q]")
        self.assertGreaterEqual(btn.width, 120)
        self.assertEqual(btn.height, 36)

    def test_collapsible_sidebar_tabs(self) -> None:
        """Verifica que la barra lateral tenga las 4 pestañas requeridas y colapse."""
        selected_tab = None
        def _on_select(t: str) -> None:
            nonlocal selected_tab
            selected_tab = t

        sidebar = FletCollapsibleGooeySidebar(
            on_tab_selected=_on_select,
            theme_manager=self.theme_mgr
        )

        tab_ids = [t[0] for t in sidebar.TAB_ITEMS]
        self.assertEqual(tab_ids, ["dashboard", "settings", "palette", "telemetry"])
        self.assertEqual(sidebar.width, 220)

        # Alternar colapso
        sidebar.toggle_collapsed()
        self.assertEqual(sidebar.width, 72)
        sidebar.toggle_collapsed()
        self.assertEqual(sidebar.width, 220)

        # Seleccionar pestaña 'palette'
        sidebar.select_tab("palette")
        self.assertEqual(selected_tab, "palette")

    def test_theme_studio_view_in_window(self) -> None:
        """Verifica que el estudio de diseño se monte como Container integrado."""
        cfg = AppConfig()
        view = FletThemeStudioView(
            theme_manager=self.theme_mgr,
            config=cfg
        )
        self.assertEqual(len(view._cards), 6)
        view._on_theme_chosen("cyan")
        self.assertEqual(self.theme_mgr.current_id, "cyan")

        # Probar botón para restaurar estilo por defecto
        view._reset_to_default_theme()
        self.assertEqual(self.theme_mgr.current_id, "default")
        self.assertEqual(view._opacity_slider.value, 1.0)
        self.assertIn("restaurado", view._toast_text.value.lower())

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
        # Debe contener los mensajes iniciales sin lanzar RuntimeError
        self.assertGreaterEqual(len(tv._log_column.controls), 2)
        # Agregar nuevo log tampoco debe lanzar excepción
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
        # safe_update no debe lanzar RuntimeError
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
        # 1. El nombre del programa debe ser 'AutoRod' y NO incluir 'v2.0'
        self.assertEqual(tb._title_text.value, "AutoRod")
        self.assertNotIn("v2.0", tb._title_text.value)

        # 2. Inicialmente el botón de actualización debe estar oculto
        self.assertFalse(tb._update_button.visible)

        # 3. Al recibir una actualización, se activa y muestra el tag
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

        # 4. Botón de cierre dispara el callback
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
        # Cambio de tema
        self.theme_mgr.set_theme("purple")
        self.assertEqual(skeleton._spinner.color, self.theme_mgr.current.primary)

    def test_collapsible_sidebar_liquid_indicator_and_shortcuts(self) -> None:
        """Verifica los atajos, el indicador líquido y el estado de la barra lateral."""
        selected = None
        def _cb(t: str) -> None:
            nonlocal selected
            selected = t

        sidebar = FletCollapsibleGooeySidebar(on_tab_selected=_cb, theme_manager=self.theme_mgr)
        self.assertEqual(len(sidebar._tab_indicators), 4)
        # El dashboard activo tiene indicador visible
        self.assertEqual(sidebar._tab_indicators["dashboard"].bgcolor, self.theme_mgr.current.primary)

        # Cambiar a configuración
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

        # 2. Tarjetas de opciones de tema sin BoxShadow
        studio = FletThemeStudioView(theme_manager=self.theme_mgr, config=AppConfig())
        for tid, card in studio._cards.items():
            self.assertIsNone(card._swatch.shadow)
            self.assertFalse(bool(emoji_pattern.findall(card._status_badge.content.value)))

        # 3. Textos y botones en ThemeStudioView
        self.assertFalse(bool(emoji_pattern.findall(studio._reset_btn._btn_text.value)))
        self.assertFalse(bool(emoji_pattern.findall(studio._sample_btn._btn_text.value)))

        # 4. Settings View sin emojis
        from autorod.infrastructure.ui.flet.components.settings_view import FletSettingsView
        settings = FletSettingsView(config=AppConfig())
        self.assertFalse(bool(emoji_pattern.findall(settings._save_btn._btn_text.value)))
        for opt in settings._backend_dropdown.options:
            self.assertFalse(bool(emoji_pattern.findall(opt.text)))

        # 5. Telemetry View sin emojis
        telemetry = FletTelemetryView(theme_manager=self.theme_mgr)
        for ctrl in telemetry._log_column.controls:
            self.assertFalse(bool(emoji_pattern.findall(ctrl.value)))

    def test_minimalist_topbar_breadcrumbs_omits_palette_and_autorod_prefix(self) -> None:
        """Verifica que el título superior sea limpio y omita prefijos redundantes y texto de paleta."""
        from autorod.infrastructure.ui.flet.app import FletMainApp
        from unittest.mock import MagicMock
        app = FletMainApp(
            runner=MagicMock(),
            diagnostics=MagicMock(),
            renderer=MagicMock(),
            config=AppConfig()
        )
        # Mock view switcher and controls
        app._breadcrumb_text = ft.Text("Dashboard")
        for tab in ("dashboard", "settings", "palette", "telemetry"):
            app._current_tab = tab
            app._update_breadcrumb_text()
            val = app._breadcrumb_text.value
            self.assertNotIn("AutoRod", val)
            self.assertNotIn("Paleta:", val)
            self.assertNotIn(" / ", val)
        self.assertEqual(app._breadcrumb_text.value, "Telemetría")

    def test_viewport_standby_and_preview_toggle(self) -> None:
        """Verifica que el viewport comience en standby con logo e indicaciones, y alterne al previsualizar."""
        vp = FletDiagnosticsViewport(theme_manager=self.theme_mgr)
        self.assertFalse(vp._is_preview_active)
        self.assertFalse(vp._is_bot_running)
        self.assertEqual(vp._center_switcher.content, vp._standby_view)
        self.assertEqual(vp.card_motor._val_text.value, "PAUSADO [Shift+Q]")

        # Activar Visualizar
        vp.set_preview_active(True)
        self.assertTrue(vp._is_preview_active)
        self.assertEqual(vp._center_switcher.content, vp._image_container)
        self.assertEqual(vp._status_text.value, "VISOR ACTIVO")

        # Desactivar Visualizar
        vp.set_preview_active(False)
        self.assertFalse(vp._is_preview_active)
        self.assertEqual(vp._center_switcher.content, vp._standby_view)

    def test_app_starts_paused_with_minimal_buttons(self) -> None:
        """Verifica que la app inicie pausada, con 3 botones útiles y sin botones innecesarios."""
        from autorod.infrastructure.ui.flet.app import FletMainApp
        from unittest.mock import MagicMock
        app = FletMainApp(
            runner=MagicMock(),
            diagnostics=MagicMock(),
            renderer=MagicMock(),
            config=AppConfig()
        )
        self.assertFalse(app._bot_running)
        self.assertFalse(app._diagnostics_active)

        # Verificar que no exista _recal_btn en la app
        self.assertFalse(hasattr(app, "_recal_btn"))

        # Montar página simulada para instanciar controles
        page = MagicMock()
        page.overlay = []
        page.add = MagicMock()
        page.theme_mode = ft.ThemeMode.DARK
        app.main(page)

        # Botones del topbar
        self.assertEqual(app._preview_btn._btn_text.value, "Visualizar")
        self.assertEqual(app._action_btn._btn_text.value, "INICIAR BOT")
        self.assertEqual(app._emergency_btn._text_ctrl.value, "SALIR [Q]")

        # Toggling preview
        app.toggle_diagnostics_feed()
        self.assertTrue(app._diagnostics_active)
        self.assertEqual(app._preview_btn._btn_text.value, "Ocultar Visor")

        # Toggling bot action
        app.toggle_bot_action()
        self.assertTrue(app._bot_running)
        self.assertEqual(app._action_btn._btn_text.value, "PAUSAR BOT")

    def test_sidebar_omits_motor_footer_and_uses_image_logo(self) -> None:
        """Verifica que la barra lateral no tenga el footer 'MOTOR ACTIVO' y cargue el logo real."""
        sidebar = FletCollapsibleGooeySidebar(on_tab_selected=lambda t: None, theme_manager=self.theme_mgr)
        self.assertFalse(hasattr(sidebar, "_footer_container"))
        self.assertFalse(hasattr(sidebar, "_footer_title"))

        # El logo debe ser un Image con ruta válida a logo.png o logo_32.png
        from autorod.infrastructure.ui.flet.utils import get_asset_path
        expected_logo = get_asset_path("icons/logo_32.png")
        self.assertTrue(expected_logo.is_file())

    def test_viewport_parameters_panel_and_clear_cache_button(self) -> None:
        """Verifica el panel de Parámetros a la derecha y el botón de flechas en bucle para vaciar caché."""
        cache_cleared = False
        def _clear_cb() -> None:
            nonlocal cache_cleared
            cache_cleared = True

        vp = FletDiagnosticsViewport(theme_manager=self.theme_mgr, on_clear_cache=_clear_cb)
        self.assertTrue(hasattr(vp, "_clear_cache_btn"))
        self.assertEqual(vp._clear_cache_btn.icon, ft.Icons.AUTORENEW_ROUNDED)

        # Accionar el botón de vaciar caché
        vp._handle_clear_cache(None)
        self.assertTrue(cache_cleared)
        self.assertEqual(vp.card_cache._val_text.value, "Recalibrando...")
        self.assertEqual(vp.card_cache._sub_text.value, "Caché purgado")

    def test_sidebar_integrated_parameters_view(self) -> None:
        """Verifica que el apartado de parámetros esté integrado en el sidebar y se visualice al abrirse."""
        from autorod.infrastructure.ui.flet.components.settings_view import FletSettingsView
        settings = FletSettingsView(config=AppConfig())
        selected_tab = ""
        def _on_select(t: str) -> None:
            nonlocal selected_tab
            selected_tab = t

        sidebar = FletCollapsibleGooeySidebar(
            on_tab_selected=_on_select,
            theme_manager=self.theme_mgr,
            settings_view=settings
        )

        # 1. En inicio, settings_container está oculto y ancho es EXPANDED_WIDTH (220)
        self.assertIsNotNone(sidebar._settings_container)
        self.assertFalse(sidebar._settings_container.visible)
        self.assertEqual(sidebar.width, 220)

        # 2. Al abrir el apartado de Configuración, se visualiza la información en el sidebar y el ancho se ajusta a 320
        sidebar.select_tab("settings")
        self.assertEqual(selected_tab, "settings")
        self.assertTrue(sidebar._settings_container.visible)
        self.assertEqual(sidebar.width, 320)
        self.assertTrue(sidebar._is_settings_open)

        # 3. Al cambiar a otra pestaña (dashboard), se oculta el panel de parámetros en el sidebar
        sidebar.select_tab("dashboard")
        self.assertEqual(selected_tab, "dashboard")
        self.assertFalse(sidebar._settings_container.visible)
        self.assertEqual(sidebar.width, 220)
        self.assertFalse(sidebar._is_settings_open)


if __name__ == "__main__":
    unittest.main()
