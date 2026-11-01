import unittest
from autorod.domain.models.fishing_state import FishingState, FishingStateMachine


class TestFishingStateMachine(unittest.TestCase):
    def setUp(self) -> None:
        self.fsm = FishingStateMachine(
            minigame_timeout_s=5.0,
            card_timeout_s=3.0
        )

    def test_initial_state_is_scanning(self) -> None:
        self.assertEqual(self.fsm.state, FishingState.SCANNING)

    def test_transitions_update_state_and_timestamp(self) -> None:
        self.fsm.transition_to(FishingState.MINIGAME, now=10.0)
        self.assertEqual(self.fsm.state, FishingState.MINIGAME)
        self.assertEqual(self.fsm.state_entered_at, 10.0)

        self.fsm.transition_to(FishingState.CARD_DISMISS, now=12.5)
        self.assertEqual(self.fsm.state, FishingState.CARD_DISMISS)
        self.assertEqual(self.fsm.state_entered_at, 12.5)

    def test_minigame_timeout_resets_to_scanning(self) -> None:
        self.fsm.transition_to(FishingState.MINIGAME, now=10.0)
        # Not yet timed out
        timed_out = self.fsm.check_timeouts(now=14.0)
        self.assertFalse(timed_out)
        self.assertEqual(self.fsm.state, FishingState.MINIGAME)

        # Timed out (> 5.0s)
        timed_out = self.fsm.check_timeouts(now=15.5)
        self.assertTrue(timed_out)
        self.assertEqual(self.fsm.state, FishingState.SCANNING)

    def test_card_timeout_resets_to_scanning(self) -> None:
        self.fsm.transition_to(FishingState.CARD_DISMISS, now=20.0)
        # Not yet timed out
        timed_out = self.fsm.check_timeouts(now=22.5)
        self.assertFalse(timed_out)
        self.assertEqual(self.fsm.state, FishingState.CARD_DISMISS)

        # Timed out (> 3.0s)
        timed_out = self.fsm.check_timeouts(now=23.5)
        self.assertTrue(timed_out)
        self.assertEqual(self.fsm.state, FishingState.SCANNING)


if __name__ == "__main__":
    unittest.main()
