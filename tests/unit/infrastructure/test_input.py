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
    def test_settings_view_has_figma_controls_and_options(self) -> None:
        """Verifica que la vista de configuración oficial de Figma 1:1 contenga todos sus controles."""
        config = AppConfig(monitor_index=1, target_fps=60)
        view = FletSettingsView(config=config)

        # 1. Pantalla de origen (Monitor)
        self.assertIsNotNone(view._monitor_dropdown)
        self.assertEqual(view._monitor_dropdown.value, "1")

        # 2. Frecuencia de captura (FPS)
        self.assertIsNotNone(view._fps_dropdown)
        self.assertEqual(view._fps_dropdown.value, "60")
        fps_values = [opt.key for opt in view._fps_dropdown.options]
        self.assertIn("30", fps_values)
        self.assertIn("60", fps_values)
        self.assertIn("120", fps_values)

        # 3. Switches de comportamiento oficial de Figma
        self.assertTrue(view._defocus_switch.value)
        self.assertTrue(view._tray_switch.value)
        self.assertFalse(view._startup_switch.value)

        # 4. Botones de acción
        self.assertIsNotNone(view._save_btn)
        self.assertIsNotNone(view._reset_btn)

    def test_settings_view_saving_and_reset(self) -> None:
        """Verifica que restablecer y guardar actualicen la configuración correctamente."""
        saved_cfg = None
        def _on_save(c: AppConfig) -> None:
            nonlocal saved_cfg
            saved_cfg = c

        config = AppConfig(monitor_index=1, target_fps=60, pause_on_defocus=True)
        view = FletSettingsView(config=config, on_save_callback=_on_save)

        # Modificar valores temporalmente
        view._fps_dropdown.value = "120"
        view._defocus_switch.value = False

        # Reset devuelve a los valores originales (60 FPS)
        view._on_reset_click(None)
        self.assertEqual(view._fps_dropdown.value, "60")
        self.assertTrue(view._defocus_switch.value)

        # Ahora modificar y guardar
        view._fps_dropdown.value = "120"
        view._defocus_switch.value = False
        view._on_save_click(None)

        self.assertIsNotNone(saved_cfg)
        self.assertEqual(saved_cfg.target_fps, 120)
        self.assertFalse(saved_cfg.pause_on_defocus)

    def test_settings_view_theme_reactivity(self) -> None:
        """Verifica que la vista responda reactivamente ante cambios de tema."""
        from autorod.infrastructure.ui.flet.theme import ThemeManager, create_theme_tokens
        theme_mgr = ThemeManager.get_instance("default")
        view = FletSettingsView(config=AppConfig(), theme_manager=theme_mgr)

        new_tokens = create_theme_tokens("light", "#5554d9")
        view.apply_theme(new_tokens)
        self.assertEqual(view._tokens.mode, "light")
        self.assertEqual(view.bgcolor, "#f2f3f8")
        self.assertEqual(view._title_text.color, "#111827")


if __name__ == "__main__":
    unittest.main()
