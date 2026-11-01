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
            card_cooldown_s=0.0,
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

        # 6. Fish caught! Blank card appears -> enters CARD_DISMISS and clicks #1
        cmds_card1 = self.task.evaluate(self._make_result("blank_card_detected"))
        self.assertEqual(len(cmds_card1), 3)
        self.assertEqual(self.task.current_state, FishingState.CARD_DISMISS)

        # 7. Card is still animating -> clicks #2 to skip flip animation
        cmds_card2 = self.task.evaluate(self._make_result("blank_card_detected"))
        self.assertEqual(len(cmds_card2), 3)
        self.assertEqual(self.task.current_state, FishingState.CARD_DISMISS)

        # 8. Card is dismissed and disappears -> transitions back to SCANNING!
        cmds_gone = self.task.evaluate(self._make_result("scanning_for_targets", found=False))
        self.assertEqual(len(cmds_gone), 0)
        self.assertEqual(self.task.current_state, FishingState.SCANNING)

    def test_disabled_task_returns_no_commands_when_paused(self) -> None:
        self.task.enabled = False
        res = self._make_result("cast_button_detected")
        commands = self.task.evaluate(res)
        self.assertEqual(len(commands), 0)

        res_needle = self._make_result("minigame_needle_hit")
        commands_needle = self.task.evaluate(res_needle)
        self.assertEqual(len(commands_needle), 0)


if __name__ == "__main__":
    unittest.main()
