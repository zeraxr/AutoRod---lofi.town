import unittest
from autorod.domain.models.fishing_state import FishingState, FishingStateMachine
from autorod.domain.models.match_result import MatchResult
from autorod.domain.models.geometry import Point, Size, Region
from autorod.domain.models.input_commands import MouseMove, MouseClick
from autorod.application.use_cases.find_and_click import FindAndClickTask


class TestFishingCycleTask(unittest.TestCase):
    def setUp(self) -> None:
        self.fsm = FishingStateMachine(minigame_timeout_s=5.0, card_timeout_s=3.0)
        self.task = FindAndClickTask(
            click_cooldown_s=0.0,
            minigame_cooldown_s=0.0,
            card_dismiss_duration_s=4.0,
            card_initial_delay_s=0.0,
            card_cooldown_s=0.0,
            max_card_dismiss_clicks=3,
            state_machine=self.fsm
        )

    def _make_result(self, strategy_id: str, found: bool = True, x: int = 100, y: int = 200) -> MatchResult:
        return MatchResult(
            found=found,
            confidence=0.9,
            region=Region(top_left=Point(x=x, y=y), size=Size(width=50, height=30)),
            center=Point(x=x + 25, y=y + 15),
            strategy_id=strategy_id,
            frame_id=1
        )

    def test_cast_button_clicks_and_stays_in_scanning(self) -> None:
        res = self._make_result("cast_button_detected")
        commands = self.task.evaluate(res)
        self.assertEqual(len(commands), 3)  # Move + Down + Up
        self.assertIsInstance(commands[0], MouseMove)
        self.assertIsInstance(commands[1], MouseClick)
        self.assertEqual(self.task.current_state, FishingState.SCANNING)

    def test_reel_button_clicks_and_transitions_to_minigame(self) -> None:
        res = self._make_result("reel_button_detected")
        commands = self.task.evaluate(res)
        self.assertEqual(len(commands), 3)
        self.assertEqual(self.task.current_state, FishingState.MINIGAME)

    def test_blank_card_is_ignored_during_scanning_state(self) -> None:
        # Crucial security guarantee: do NOT click white cards during normal scanning
        self.assertEqual(self.task.current_state, FishingState.SCANNING)
        res = self._make_result("blank_card_detected")
        commands = self.task.evaluate(res)
        self.assertEqual(len(commands), 0)
        self.assertEqual(self.task.current_state, FishingState.SCANNING)

    def test_full_successful_fishing_cycle_with_multi_click_card_dismiss(self) -> None:
        # 1. Cast
        cmds_cast = self.task.evaluate(self._make_result("cast_button_detected"))
        self.assertEqual(len(cmds_cast), 3)
        self.assertEqual(self.task.current_state, FishingState.SCANNING)

        # 2. Reel
        cmds_reel = self.task.evaluate(self._make_result("reel_button_detected"))
        self.assertEqual(len(cmds_reel), 3)
        self.assertEqual(self.task.current_state, FishingState.MINIGAME)

        # 3. Minigame tracking (needle not yet in green zone) -> no clicks!
        cmds_tracking = self.task.evaluate(self._make_result("minigame_tracking", found=False))
        self.assertEqual(len(cmds_tracking), 0)
        self.assertEqual(self.task.current_state, FishingState.MINIGAME)

        # 4. Minigame needle hit #1 -> clicks and stays in MINIGAME (pulling rod closer)
        cmds_hit1 = self.task.evaluate(self._make_result("minigame_needle_hit"))
        self.assertEqual(len(cmds_hit1), 3)
        self.assertEqual(self.task.current_state, FishingState.MINIGAME)

        # 5. Minigame needle hit #2 -> clicks again and stays in MINIGAME
        cmds_hit2 = self.task.evaluate(self._make_result("minigame_needle_hit"))
        self.assertEqual(len(cmds_hit2), 3)
        self.assertEqual(self.task.current_state, FishingState.MINIGAME)

        # 6. Fish caught! Blank card appears -> enters CARD_DISMISS (settle wait, returns [])
        cmds_card_init = self.task.evaluate(self._make_result("blank_card_detected"))
        self.assertEqual(len(cmds_card_init), 0)
        self.assertEqual(self.task.current_state, FishingState.CARD_DISMISS)

        # 7. Settle wait complete -> clicks #1 in CARD_DISMISS
        cmds_card1 = self.task.evaluate(self._make_result("blank_card_detected"))
        self.assertEqual(len(cmds_card1), 3)
        self.assertEqual(self.task.current_state, FishingState.CARD_DISMISS)

        # 8. Card animating (flipping) -> clicks #2
        cmds_card2 = self.task.evaluate(self._make_result("scanning_for_targets", found=False))
        self.assertEqual(len(cmds_card2), 3)
        self.assertEqual(self.task.current_state, FishingState.CARD_DISMISS)

        # 9. Card continues -> clicks #3 (burst limit reached)
        cmds_card3 = self.task.evaluate(self._make_result("scanning_for_targets", found=False))
        self.assertEqual(len(cmds_card3), 3)
        self.assertEqual(self.task.current_state, FishingState.CARD_DISMISS)

        # 10. Burst limit reached -> no more clicks emitted (prevents clicking player avatars!)
        cmds_stopped = self.task.evaluate(self._make_result("scanning_for_targets", found=False))
        self.assertEqual(len(cmds_stopped), 0)
        self.assertEqual(self.task.current_state, FishingState.CARD_DISMISS)

        # 11. CAST! reappears or duration finishes -> transitions to SCANNING
        cmds_cast = self.task.evaluate(self._make_result("cast_button_detected"))
        self.assertEqual(len(cmds_cast), 3)
        self.assertEqual(self.task.current_state, FishingState.SCANNING)

    def test_card_dismiss_ends_immediately_when_cast_button_reappears(self) -> None:
        # Move to MINIGAME and trigger CARD_DISMISS
        self.task.evaluate(self._make_result("reel_button_detected"))
        self.task.evaluate(self._make_result("blank_card_detected"))
        self.assertEqual(self.task.current_state, FishingState.CARD_DISMISS)

        # In mid-burst, if CAST! button reappears, it should immediately transition to SCANNING and click CAST!
        cmds_cast = self.task.evaluate(self._make_result("cast_button_detected"))
        self.assertEqual(len(cmds_cast), 3)
        self.assertEqual(self.task.current_state, FishingState.SCANNING)

    def test_disabled_task_returns_no_commands_when_paused(self) -> None:
        self.task.enabled = False
        res = self._make_result("cast_button_detected")
        commands = self.task.evaluate(res)
        self.assertEqual(len(commands), 0)

        res_needle = self._make_result("minigame_needle_hit")
        commands_needle = self.task.evaluate(res_needle)
        self.assertEqual(len(commands_needle), 0)

    def test_card_dismiss_synthetic_ticks_drive_clicks_continuously(self) -> None:
        """Verifica que ticks sintéticos (cola vacía) sigan emitiendo clics en CARD_DISMISS."""
        task = FindAndClickTask(
            click_cooldown_s=0.0,
            minigame_cooldown_s=0.0,
            card_dismiss_duration_s=4.0,
            card_initial_delay_s=0.0,
            card_cooldown_s=0.0,
            max_card_dismiss_clicks=3,
            state_machine=FishingStateMachine()
        )
        # 1. Picar pez e ir a minijuego
        task.evaluate(self._make_result("reel_button_detected"))
        self.assertEqual(task.current_state, FishingState.MINIGAME)

        # 2. Tarjeta blanca detectada -> entra a CARD_DISMISS (asentamiento de entrada, sin clics iniciales)
        cmds_appear = task.evaluate(self._make_result("blank_card_detected", x=500, y=300))
        self.assertEqual(len(cmds_appear), 0)
        self.assertEqual(task.current_state, FishingState.CARD_DISMISS)

        # 3. La visión no encuentra tarjeta (cola vacía / tick sintético) -> emite clic #1 memorizando coordenadas
        cmds_tick1 = task.evaluate(MatchResult(found=False, confidence=0.0, strategy_id="card_dismiss_tick"))
        self.assertEqual(len(cmds_tick1), 3)
        self.assertEqual(cmds_tick1[0].x, 525)  # Memorizó el centro x=500+25
        self.assertEqual(cmds_tick1[0].y, 315)  # y=300+15
        self.assertEqual(task.current_state, FishingState.CARD_DISMISS)

        # 4. Segundo tick sintético -> emite clic #2
        cmds_tick2 = task.evaluate(MatchResult(found=False, confidence=0.0, strategy_id="card_dismiss_tick"))
        self.assertEqual(len(cmds_tick2), 3)
        self.assertEqual(task.current_state, FishingState.CARD_DISMISS)

        # 5. Tercer tick sintético -> emite clic #3 (límite de clics alcanzado)
        cmds_tick3 = task.evaluate(MatchResult(found=False, confidence=0.0, strategy_id="card_dismiss_tick"))
        self.assertEqual(len(cmds_tick3), 3)
        self.assertEqual(task.current_state, FishingState.CARD_DISMISS)

        # 6. Cuarto tick sintético -> límite alcanzado, clics detenidos (no clica avatares)
        cmds_tick4 = task.evaluate(MatchResult(found=False, confidence=0.0, strategy_id="card_dismiss_tick"))
        self.assertEqual(len(cmds_tick4), 0)
        self.assertEqual(task.current_state, FishingState.CARD_DISMISS)

    def test_v110_three_phase_card_dismiss_cadence(self) -> None:
        """Verifica la secuencia exacta de 3 fases de AutoRod v1.1.0."""
        import time
        from unittest.mock import patch

        task = FindAndClickTask(
            click_cooldown_s=0.35,
            minigame_cooldown_s=0.22,
            card_dismiss_duration_s=1.60,
            card_initial_delay_s=0.50,
            card_cooldown_s=0.12,
            max_card_dismiss_clicks=5,
            state_machine=FishingStateMachine()
        )
        with patch("time.monotonic", return_value=99.0):
            task.evaluate(self._make_result("reel_button_detected"))
            self.assertEqual(task.current_state, FishingState.MINIGAME)

        # Inicia a t = 100.0
        with patch("time.monotonic", return_value=100.0):
            # Fase 1: Detección inicial -> Entra a CARD_DISMISS pero espera 0.5s sin clics
            c = task.evaluate(self._make_result("blank_card_detected", x=300, y=200))
            self.assertEqual(len(c), 0)
            self.assertEqual(task.current_state, FishingState.CARD_DISMISS)

        # En t = 100.3 (0.3s transcurridos, aún en Fase 1) -> NO debe cliquear
        with patch("time.monotonic", return_value=100.3):
            c = task.evaluate(self._make_result("blank_card_detected", x=300, y=200))
            self.assertEqual(len(c), 0)

        # En t = 100.51 (Fase 2: Asentamiento cumplido) -> Clic #1
        with patch("time.monotonic", return_value=100.51):
            c = task.evaluate(self._make_result("blank_card_detected", x=300, y=200))
            self.assertEqual(len(c), 3)

        # En t = 100.55 (Cooldown de 120ms no cumplido) -> Espera
        with patch("time.monotonic", return_value=100.55):
            c = task.evaluate(self._make_result("blank_card_detected", x=300, y=200))
            self.assertEqual(len(c), 0)

        # En t = 100.64 (130ms después de Clic #1) -> Clic #2
        with patch("time.monotonic", return_value=100.64):
            c = task.evaluate(self._make_result("blank_card_detected", x=300, y=200))
            self.assertEqual(len(c), 3)

        # Clics #3, #4, #5
        with patch("time.monotonic", return_value=100.77):
            c = task.evaluate(self._make_result("blank_card_detected", x=300, y=200))
            self.assertEqual(len(c), 3)
        with patch("time.monotonic", return_value=100.90):
            c = task.evaluate(self._make_result("blank_card_detected", x=300, y=200))
            self.assertEqual(len(c), 3)
        with patch("time.monotonic", return_value=101.03):
            c = task.evaluate(self._make_result("blank_card_detected", x=300, y=200))
            self.assertEqual(len(c), 3)

        # Fase 3: Ya se emitieron 5 clics. En t = 101.20 (después del 5to clic) -> ¡CERO CLICS!
        with patch("time.monotonic", return_value=101.20):
            c = task.evaluate(self._make_result("blank_card_detected", x=300, y=200))
            self.assertEqual(len(c), 0)
            self.assertEqual(task.current_state, FishingState.CARD_DISMISS)

        # Fin de secuencia en t = 101.65 (>= 1.60s) -> Transición a SCANNING
        with patch("time.monotonic", return_value=101.65):
            c = task.evaluate(self._make_result("blank_card_detected", x=300, y=200))
            self.assertEqual(len(c), 0)
            self.assertEqual(task.current_state, FishingState.SCANNING)


if __name__ == "__main__":
    unittest.main()
