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
        self.assertEqual(btn._btn_text.value, "✓ EJECUTADO")

    def test_emergency_button_bounds_prevent_clipping(self) -> None:
        """Verifica que el botón de emergencia en Flet tenga medidas seguras contra recorte."""
        btn = FletKineticEmergencyButton(
            on_click=lambda: None,
            text="🚨 SALIR [Q]",
            width=130,
            height=36
        )
        self.assertEqual(btn._text_ctrl.value, "🚨 SALIR [Q]")
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
        self.assertEqual(view._opacity_slider.value, 0.96)
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


if __name__ == "__main__":
    unittest.main()
