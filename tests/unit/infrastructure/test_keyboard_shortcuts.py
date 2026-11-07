import unittest
from unittest.mock import MagicMock, patch
import flet as ft
from autorod.infrastructure.ui.flet.app import FletMainApp
from autorod.config import AppConfig


class TestKeyboardShortcuts(unittest.TestCase):
    def setUp(self) -> None:
        self.runner = MagicMock()
        self.runner.supervisor = MagicMock()
        self.runner.supervisor.executor = MagicMock()
        self.diag_sink = MagicMock()
        self.renderer = MagicMock()
        self.vision_strategy = MagicMock()
        self.capture_source = MagicMock()
        self.config = AppConfig()

        self.app = FletMainApp(
            runner=self.runner,
            diagnostics=self.diag_sink,
            renderer=self.renderer,
            vision_strategy=self.vision_strategy,
            capture_source=self.capture_source,
            config=self.config
        )

    def test_plain_q_does_not_trigger_emergency_shutdown(self) -> None:
        """Verifica que presionar solo 'Q' NO active el apagado de emergencia."""
        self.app.emergency_shutdown = MagicMock()
        self.app.toggle_bot_action = MagicMock()

        evt = MagicMock(key="q", shift=False, alt=False)
        self.app._on_flet_key_event(evt)

        self.app.emergency_shutdown.assert_not_called()
        self.app.toggle_bot_action.assert_not_called()

    def test_left_alt_plus_q_triggers_emergency_shutdown(self) -> None:
        """Verifica que 'LEFT ALT + Q' active el apagado de emergencia."""
        self.app.emergency_shutdown = MagicMock()

        evt = MagicMock(key="q", shift=False, alt=True)
        self.app._on_flet_key_event(evt)

        self.app.emergency_shutdown.assert_called_once()

    def test_shift_plus_q_triggers_bot_toggle(self) -> None:
        """Verifica que 'SHIFT + Q' alterne el modo de pausa."""
        self.app.toggle_bot_action = MagicMock()
        self.app.emergency_shutdown = MagicMock()

        evt = MagicMock(key="q", shift=True, alt=False)
        self.app._on_flet_key_event(evt)

        self.app.toggle_bot_action.assert_called_once()
        self.app.emergency_shutdown.assert_not_called()

    def test_f8_does_not_trigger_action(self) -> None:
        """Verifica que 'F8' no dispare acciones (atajo no implementado aún)."""
        self.app.toggle_bot_action = MagicMock()
        evt = MagicMock(key="f8", shift=False, alt=False)
        self.app._on_flet_key_event(evt)
        self.app.toggle_bot_action.assert_not_called()

    def test_f9_does_not_trigger_action(self) -> None:
        """Verifica que 'F9' no dispare acciones (atajo no implementado aún)."""
        self.app._bot_running = True
        self.app.toggle_bot_action = MagicMock()
        evt = MagicMock(key="f9", shift=False, alt=False)
        self.app._on_flet_key_event(evt)
        self.app.toggle_bot_action.assert_not_called()

    def test_unpausing_bot_automatically_purges_scale_cache(self) -> None:
        """Verifica que al reanudar el bot se purgue automáticamente la memoria de escala."""
        self.app._bot_running = False
        self.app.toggle_bot_action()

        self.assertTrue(self.app._bot_running)
        self.vision_strategy.clear_scale_cache.assert_called_once()


if __name__ == "__main__":
    unittest.main()
