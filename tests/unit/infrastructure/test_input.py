"""Pruebas unitarias para el subsistema de inyección de entrada y simuladores Win32."""

import unittest
from unittest.mock import MagicMock, call
import ctypes
from ctypes import wintypes

from autorod.domain.models.input_commands import (
    MouseMove,
    MouseClick,
    MouseButton,
)
from autorod.infrastructure.input.factory import InputBackendFactory
from autorod.infrastructure.input.fake_input import FakeInputSimulator
from autorod.infrastructure.input.win32.sendinput import SendInputSimulator
from autorod.infrastructure.input.win32.postmessage import (
    Win32PostMessageSimulator,
    WM_MOUSEMOVE,
    WM_LBUTTONDOWN,
    WM_LBUTTONUP,
    WM_RBUTTONDOWN,
    WM_RBUTTONUP,
    WM_MBUTTONDOWN,
    WM_MBUTTONUP,
    MK_LBUTTON,
    MK_RBUTTON,
    MK_MBUTTON,
    POINT,
    RECT
)
from autorod.infrastructure.ui.flet.components.settings_view import FletSettingsView
from autorod.config import AppConfig


class TestInputBackendFactory(unittest.TestCase):
    def test_factory_creates_expected_backends(self) -> None:
        """Verifica que la factoría resuelva los backends y sus alias."""
        fake = InputBackendFactory.create("fake")
        self.assertIsInstance(fake, FakeInputSimulator)

        mock_sim = InputBackendFactory.create("mock")
        self.assertIsInstance(mock_sim, FakeInputSimulator)

        legacy = InputBackendFactory.create("sendinput")
        self.assertIsInstance(legacy, SendInputSimulator)

        legacy_alias = InputBackendFactory.create("legacy")
        self.assertIsInstance(legacy_alias, SendInputSimulator)

        novo = InputBackendFactory.create("postmessage")
        self.assertIsInstance(novo, Win32PostMessageSimulator)

        novo_alias = InputBackendFactory.create("nuevo")
        self.assertIsInstance(novo_alias, Win32PostMessageSimulator)

        bg_alias = InputBackendFactory.create("background")
        self.assertIsInstance(bg_alias, Win32PostMessageSimulator)

    def test_factory_raises_value_error_for_unknown(self) -> None:
        """Verifica que backends desconocidos lancen ValueError descriptivo."""
        with self.assertRaises(ValueError):
            InputBackendFactory.create("non_existent_backend_xyz")


class TestWin32PostMessageSimulator(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_user32 = MagicMock()
        self.simulator = Win32PostMessageSimulator(user32=self.mock_user32)

    def test_mouse_move_sends_post_message(self) -> None:
        """Verifica que MouseMove resuelva la ventana y envíe WM_MOUSEMOVE con coordenadas cliente."""
        self.mock_user32.WindowFromPoint.return_value = 12345
        # ScreenToClient transforma pt en cliente (ej: x=100, y=50)
        def mock_screen_to_client(hwnd, pt_byref):
            pt_byref._obj.x = 100
            pt_byref._obj.y = 50
            return 1
        self.mock_user32.ScreenToClient.side_effect = mock_screen_to_client

        cmd = MouseMove(x=1920 + 100, y=50)
        self.simulator.execute(cmd)

        expected_lparam = (50 << 16) | 100
        self.mock_user32.PostMessageW.assert_called_with(
            12345, WM_MOUSEMOVE, 0, expected_lparam
        )

    def test_mouse_click_batch_sends_down_and_up_with_virtual_move(self) -> None:
        """Verifica que el clic envíe WM_MOUSEMOVE, WM_LBUTTONDOWN y WM_LBUTTONUP."""
        self.mock_user32.WindowFromPoint.return_value = 99999
        def mock_screen_to_client(hwnd, pt_byref):
            pt_byref._obj.x = 200
            pt_byref._obj.y = 150
            return 1
        self.mock_user32.ScreenToClient.side_effect = mock_screen_to_client

        commands = [
            MouseMove(x=200, y=150),
            MouseClick(button=MouseButton.LEFT, pressed=True),
            MouseClick(button=MouseButton.LEFT, pressed=False)
        ]
        self.simulator.execute_batch(commands)

        expected_lparam = (150 << 16) | 200
        calls = self.mock_user32.PostMessageW.call_args_list

        down_call = call(99999, WM_LBUTTONDOWN, MK_LBUTTON, expected_lparam)
        up_call = call(99999, WM_LBUTTONUP, 0, expected_lparam)
        self.assertIn(down_call, calls)
        self.assertIn(up_call, calls)

    def test_click_hold_duration_waits_between_down_and_up(self) -> None:
        """Verifica que el simulador espere el tiempo de pulsación (dwell time) entre DOWN y UP."""
        mock_event = MagicMock()
        sim = Win32PostMessageSimulator(user32=self.mock_user32, click_hold_s=0.050, cancel_event=mock_event)
        self.mock_user32.WindowFromPoint.return_value = 11111

        commands = [
            MouseClick(button=MouseButton.LEFT, pressed=True),
            MouseClick(button=MouseButton.LEFT, pressed=False)
        ]
        sim.execute_batch(commands)
        mock_event.wait.assert_called_once_with(timeout=0.050)

    def test_right_and_middle_click(self) -> None:
        """Verifica el envío de clics derecho y central con movimiento previo."""
        self.mock_user32.WindowFromPoint.return_value = 54321
        def mock_screen_to_client(hwnd, pt_byref):
            pt_byref._obj.x = 10
            pt_byref._obj.y = 20
            return 1
        self.mock_user32.ScreenToClient.side_effect = mock_screen_to_client

        self.simulator.execute(MouseMove(x=10, y=20))
        self.simulator.execute(MouseClick(button=MouseButton.RIGHT, pressed=True))
        lparam = (20 << 16) | 10
        self.mock_user32.PostMessageW.assert_called_with(
            54321, WM_RBUTTONDOWN, MK_RBUTTON, lparam
        )

        self.simulator.execute(MouseClick(button=MouseButton.MIDDLE, pressed=True))
        self.mock_user32.PostMessageW.assert_called_with(
            54321, WM_MBUTTONDOWN, MK_MBUTTON, lparam
        )


class TestSettingsViewTooltipsAndModes(unittest.TestCase):
    def test_settings_view_has_all_tooltips_and_modes(self) -> None:
        """Verifica que cada opción en la vista de configuración tenga su tooltip descriptivo."""
        config = AppConfig(input_backend="postmessage")
        view = FletSettingsView(config=config)

        # 1. Modo de Clics
        self.assertIsNotNone(view._backend_dropdown.tooltip)
        self.assertIn("PostMessage", view._backend_dropdown.tooltip)
        self.assertIn("SendInput", view._backend_dropdown.tooltip)

        # Verificar opciones del dropdown
        option_keys = [opt.key for opt in view._backend_dropdown.options]
        self.assertIn("postmessage", option_keys)
        self.assertIn("sendinput", option_keys)
        self.assertEqual(view._backend_dropdown.value, "postmessage")

        # 2. Monitor de Captura
        self.assertIsNotNone(view._monitor_dropdown.tooltip)
        self.assertIn("juego", view._monitor_dropdown.tooltip.lower())

        # 3. Guardar tamaño (Caché de resolución)
        self.assertIsNotNone(view._cache_switch.tooltip)
        self.assertIn("cpu", view._cache_switch.tooltip.lower())

        # 4. Sensibilidad de detección
        self.assertIsNotNone(view._thresh_slider.tooltip)
        self.assertIn("0.63", view._thresh_slider.tooltip)

        # 5. Entrada humanizada
        self.assertIsNotNone(view._humanized_switch.tooltip)
        self.assertIn("humanizado", view._humanized_switch.tooltip.lower())

        # 6. Botón de guardado
        self.assertIsNotNone(view._save_btn.tooltip)
        self.assertIn("guardar", view._save_btn.tooltip.lower())

    def test_settings_view_visual_tracking_cards_and_hints(self) -> None:
        """Verifica la jerarquía visual de la industria: anclas de icono, hint boxes y tracking tipográfico."""
        config = AppConfig()
        view = FletSettingsView(config=config)

        # 5 Anclas de icono para el escaneo vertical en el rail izquierdo
        self.assertEqual(len(view._icon_anchors), 5)
        for anchor in view._icon_anchors:
            self.assertEqual(anchor.width, 26)
            self.assertEqual(anchor.height, 26)
            self.assertEqual(anchor.border_radius, 6)

        # 5 Cajas de hint técnico contextual limpio
        self.assertEqual(len(view._hint_boxes), 5)

    def test_settings_view_live_visual_tracking_updates(self) -> None:
        """Verifica que el slider y los selectores ofrezcan feedback visual en tiempo real."""
        config = AppConfig(button_threshold=0.63, input_backend="postmessage")
        view = FletSettingsView(config=config)

        # 1. Slider en 0.63 (Óptimo)
        view._update_slider_badge(0.63)
        self.assertIn("Óptimo", view._slider_status_text.value)

        # Slider en 0.50 (Sensible)
        view._update_slider_badge(0.50)
        self.assertIn("Sensible", view._slider_status_text.value)

        # Slider en 0.78 (Estricto)
        view._update_slider_badge(0.78)
        self.assertIn("Estricto", view._slider_status_text.value)

        # 2. Notas dinámicas de backend
        view._update_backend_note("postmessage")
        self.assertIn("Silencioso", view._backend_active_note.value)

        view._update_backend_note("sendinput")
        self.assertIn("Físico", view._backend_active_note.value)

        view._update_backend_note("interception")
        self.assertIn("Kernel", view._backend_active_note.value)

    def test_settings_view_theme_reactivity(self) -> None:
        """Verifica que la vista actualice los acentos de hints ante cambios en la paleta."""
        from autorod.infrastructure.ui.flet.theme import ThemeManager
        theme_mgr = ThemeManager.get_instance("default")
        view = FletSettingsView(config=AppConfig(), theme_manager=theme_mgr)

        theme_mgr.set_theme("red")
        self.assertEqual(view._tokens.id, "red")
        for anchor in view._icon_anchors:
            self.assertEqual(anchor.content.color, view._tokens.primary)

        # Restaurar tema default
        theme_mgr.set_theme("default")
        self.assertEqual(view._tokens.id, "default")
        for anchor in view._icon_anchors:
            self.assertEqual(anchor.content.color, view._tokens.primary)
        for hint_box in view._hint_boxes:
            self.assertEqual(hint_box.border.left.color, view._tokens.primary)


if __name__ == "__main__":
    unittest.main()
