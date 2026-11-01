import queue
import unittest
from typing import Any
from autorod.domain.models.geometry import Point, Size, Region
from autorod.domain.models.match_result import MatchResult
from autorod.domain.models.input_commands import MouseMove, MouseClick, MouseButton
from autorod.application.pipeline.queues import LatestFrameQueue
from autorod.application.pipeline.producer import CaptureProducer
from autorod.application.pipeline.consumer import VisionConsumer
from autorod.application.pipeline.executor import ActionExecutor
from autorod.application.pipeline.supervisor import PipelineSupervisor
from autorod.infrastructure.clock.system_clock import SystemClock
from autorod.infrastructure.capture.fake_capture import FakeCaptureSource
from autorod.infrastructure.vision.fake_vision import FakeVisionStrategy
from autorod.infrastructure.diagnostics.queue_sink import QueueDiagnosticsSink
from autorod.infrastructure.input.fake_input import FakeInputSimulator
from autorod.application.use_cases.find_and_click import FindAndClickTask


class TestPipelineFlow(unittest.TestCase):

    def test_find_and_click_moves_mouse_to_target_and_clicks(self) -> None:
        task = FindAndClickTask(click_cooldown_s=0.1)
        target_center = Point(x=450, y=320)
        result = MatchResult(
            found=True,
            confidence=0.95,
            region=Region(top_left=Point(x=400, y=300), size=Size(width=100, height=40)),
            center=target_center,
            strategy_id="button_detected",
            frame_id=1
        )

        commands = task.evaluate(result)
        self.assertEqual(len(commands), 3)
        self.assertIsInstance(commands[0], MouseMove)
        self.assertEqual(commands[0].x, 450)  # type: ignore
        self.assertEqual(commands[0].y, 320)  # type: ignore
        self.assertTrue(commands[0].absolute)  # type: ignore

        self.assertIsInstance(commands[1], MouseClick)
        self.assertEqual(commands[1].button, MouseButton.LEFT)  # type: ignore
        self.assertTrue(commands[1].pressed)  # type: ignore

        self.assertIsInstance(commands[2], MouseClick)
        self.assertEqual(commands[2].button, MouseButton.LEFT)  # type: ignore
        self.assertFalse(commands[2].pressed)  # type: ignore

    def test_find_and_click_debounce(self) -> None:
        task = FindAndClickTask(click_cooldown_s=0.5)
        result = MatchResult(
            found=True,
            confidence=0.90,
            region=None,
            center=Point(x=100, y=100),
            strategy_id="test",
            frame_id=1
        )
        first_calls = task.evaluate(result)
        self.assertEqual(len(first_calls), 3)

        # Inmediatamente después (cooldown activo) no debe disparar
        immediate_calls = task.evaluate(result)
        self.assertEqual(len(immediate_calls), 0)

    def test_action_executor_enable_toggle(self) -> None:
        simulator = FakeInputSimulator()
        action_q: queue.Queue[Any] = queue.Queue()
        task = FindAndClickTask()
        executor = ActionExecutor(action_q, task, simulator, enabled=False)

        # Cuando está deshabilitado, no inyecta en el simulador
        result = MatchResult(
            found=True,
            confidence=1.0,
            region=None,
            center=Point(x=10, y=10),
            strategy_id="test",
            frame_id=1
        )
        commands = task.evaluate(result)
        self.assertTrue(len(commands) > 0)
        self.assertFalse(executor.is_enabled)
        self.assertFalse(executor.enabled)

        # Test property setter
        executor.enabled = True
        self.assertTrue(executor.enabled)
        self.assertTrue(executor.is_enabled)

        executor.enabled = False
        self.assertFalse(executor.enabled)

    def test_pipeline_lifecycle_orderly_shutdown(self) -> None:
        clock = SystemClock()
        source = FakeCaptureSource()
        vision = FakeVisionStrategy()
        sink = QueueDiagnosticsSink()
        task = FindAndClickTask()
        simulator = FakeInputSimulator()

        frame_q: LatestFrameQueue[Any] = LatestFrameQueue(maxsize=1)
        action_q: queue.Queue[Any] = queue.Queue(maxsize=5)

        producer = CaptureProducer(source, frame_q, clock, target_fps=60)
        consumer = VisionConsumer(vision, frame_q, action_q, sink)
        executor = ActionExecutor(action_q, task, simulator)

        supervisor = PipelineSupervisor(producer, consumer, executor)

        with supervisor:
            pass

        self.assertEqual(len(supervisor._threads), 0)


if __name__ == "__main__":
    unittest.main()
