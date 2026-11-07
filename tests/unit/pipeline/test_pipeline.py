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

    def test_vision_consumer_idle_when_disabled_and_no_preview(self) -> None:
        """Verifica que VisionConsumer no analice ni gaste CPU mientras el bot está en pausa."""
        import threading
        from unittest.mock import MagicMock
        from autorod.application.pipeline.queues import _STOP

        vision = MagicMock()
        frame_q: LatestFrameQueue[Any] = LatestFrameQueue(maxsize=1)
        action_q: queue.Queue[Any] = queue.Queue(maxsize=5)
        sink = QueueDiagnosticsSink()

        consumer = VisionConsumer(vision, frame_q, action_q, sink, enabled=False)
        self.assertFalse(consumer.enabled)
        self.assertFalse(consumer.preview_enabled)

        # Enviar un fotograma simulado con el bot pausado
        fake_payload = MagicMock()
        frame_q.put_latest(fake_payload)
        frame_q.put_latest(_STOP)

        # Ejecutar el consumidor
        consumer.run()

        # Al estar pausado y sin preview, NO debe llamar a analyze (0% CPU y sin tocar caché)
        vision.analyze.assert_not_called()
        self.assertEqual(action_q.qsize(), 1)  # Solo el _STOP

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

    def test_action_executor_card_dismiss_empty_queue_ticks(self) -> None:
        """Verifica que ActionExecutor siga disparando clics en CARD_DISMISS con cola vacía."""
        import threading
        from autorod.domain.models.fishing_state import FishingState
        from autorod.application.pipeline.queues import _STOP

        simulator = FakeInputSimulator()
        action_q: queue.Queue[Any] = queue.Queue()
        task = FindAndClickTask(
            click_cooldown_s=0.0,
            card_cooldown_s=0.0,
            card_initial_delay_s=0.0,
            card_dismiss_duration_s=4.0,
            max_card_dismiss_clicks=5
        )
        # Forzar estado CARD_DISMISS y posición conocida con timestamp actual
        import time
        now = time.monotonic()
        task._fsm.transition_to(FishingState.CARD_DISMISS, now)
        task._card_dismiss_start = now
        task._last_card_center = Point(x=300, y=400)

        executor = ActionExecutor(action_q, task, simulator, enabled=True)
        th = threading.Thread(target=executor.run, daemon=True)
        th.start()

        # Esperar activamente a que el bucle de timeout de cola vacía despache los clics
        for _ in range(30):
            if len(simulator.history) > 0:
                break
            threading.Event().wait(0.05)

        # Detener executor
        action_q.put(_STOP)
        th.join(timeout=3.0)

        # Debe haber inyectado clics generados por los ticks de cola vacía
        self.assertTrue(len(simulator.history) > 0)
        self.assertEqual(simulator.history[0].x, 300)
        self.assertEqual(simulator.history[0].y, 400)

    def test_action_executor_empty_queue_recovers_from_minigame_timeout(self) -> None:
        """Verifica que ActionExecutor permita recuperar estados atascados mediante latidos en cola vacía."""
        import threading
        import time
        from autorod.domain.models.fishing_state import FishingState, FishingStateMachine
        from autorod.application.pipeline.queues import _STOP

        simulator = FakeInputSimulator()
        action_q: queue.Queue[Any] = queue.Queue()
        fsm = FishingStateMachine(minigame_timeout_s=0.1, card_timeout_s=0.1)
        task = FindAndClickTask(state_machine=fsm)

        # Forzar estado MINIGAME en el pasado para que esté vencido
        past = time.monotonic() - 0.5
        task._fsm.transition_to(FishingState.MINIGAME, past)
        self.assertEqual(task.current_state, FishingState.MINIGAME)

        executor = ActionExecutor(action_q, task, simulator, enabled=True)
        th = threading.Thread(target=executor.run, daemon=True)
        th.start()

        # Esperar activamente a que el bucle de cola vacía despache el latido de recuperación
        for _ in range(30):
            if task.current_state == FishingState.SCANNING:
                break
            threading.Event().wait(0.05)

        action_q.put(_STOP)
        th.join(timeout=3.0)

        # El FSM debe haberse recuperado automáticamente a SCANNING gracias al latido
        self.assertEqual(task.current_state, FishingState.SCANNING)


    def test_capture_producer_transient_error_resilience(self) -> None:
        """Verifica que fallos transitorios en grab() no maten el productor y se recupere."""
        import threading
        from unittest.mock import MagicMock
        from autorod.domain.models.image_payload import ImagePayload, PixelFormat

        source = MagicMock()
        payload = ImagePayload(
            width=10, height=10, pixel_format=PixelFormat.BGR8,
            stride=30, data=b"x" * 300, frame_id=1,
            captured_at_ns=1000, source_id="test"
        )
        # 2 fallos transitorios y luego éxito
        source.grab.side_effect = [RuntimeError("BitBlt transient fail"), RuntimeError("BitBlt transient fail"), payload]

        clock = SystemClock()
        frame_q: LatestFrameQueue[Any] = LatestFrameQueue(maxsize=1)
        producer = CaptureProducer(source, frame_q, clock, target_fps=120)

        th = threading.Thread(target=producer.run, daemon=True)
        th.start()

        # Esperar a que se procese el fotograma exitoso
        item = None
        for _ in range(30):
            try:
                item = frame_q.get(timeout=0.05)
                if item is not None and item != _STOP:
                    break
            except Exception:
                pass

        producer.stop()
        th.join(timeout=2.0)

        self.assertEqual(item, payload)


if __name__ == "__main__":
    unittest.main()
