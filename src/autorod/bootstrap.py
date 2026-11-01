import queue
import logging
from typing import Any
from autorod.config import load_config, AppConfig
from autorod.infrastructure.clock.system_clock import SystemClock
from autorod.infrastructure.capture.mss_capture import MssCaptureSource
from autorod.infrastructure.capture.fake_capture import FakeCaptureSource
from autorod.infrastructure.vision.geometric_strategy import GeometricVisionStrategy
from autorod.infrastructure.vision.hsv_contour_strategy import HsvContourStrategy
from autorod.infrastructure.vision.template_match_strategy import TemplateMatchStrategy
from autorod.infrastructure.vision.fake_vision import FakeVisionStrategy
from autorod.infrastructure.diagnostics.queue_sink import QueueDiagnosticsSink
from autorod.infrastructure.imaging.annotator import OpenCVAnnotator
from autorod.infrastructure.input.factory import InputBackendFactory
from autorod.infrastructure.input.humanized import HumanizedInputSimulator
from autorod.infrastructure.ui.flet.app import FletMainApp
from autorod.application.pipeline.queues import LatestFrameQueue
from autorod.application.pipeline.producer import CaptureProducer
from autorod.application.pipeline.consumer import VisionConsumer
from autorod.application.pipeline.executor import ActionExecutor
from autorod.application.pipeline.supervisor import PipelineSupervisor
from autorod.application.pipeline.threaded_runner import ThreadedPipelineRunner
from autorod.application.use_cases.find_and_click import FindAndClickTask
from autorod.infrastructure.logging import configure_sota_logging

logger = logging.getLogger(__name__)


def build_app(config_path: str = "config.toml") -> FletMainApp:
    """
    Composition Root SOTA. Resuelve el grafo de dependencias de la aplicación:
      - Inicializa el sistema de registro industrial SOTA ('logs/autorod.log').
      - Ingesta física MSS a 60 FPS con DPI awareness.
      - Motor geométrico adaptativo para detección de aguja y botones ('Cast' / 'Reel').
      - Despacho de clics y posicionamiento automático de ratón en pantalla (FindAndClickTask).
      - UI moderna responsiva en Flet (Flutter) con Dark Mode inmersivo y ventana 'Always on Top'.
    """
    configure_sota_logging()
    config: AppConfig = load_config(config_path)
    logger.info(
        "[BOOTSTRAP] AutoRod iniciado | Monitor: %d | FPS: %d | Visión: %s | Entrada: %s",
        config.monitor_index,
        config.target_fps,
        config.vision_strategy,
        config.input_backend
    )
    clock = SystemClock()

    # 1. Ingesta de Fotogramas Real (MSS) con fallback de seguridad a sintético
    try:
        capture_source = MssCaptureSource(monitor_index=config.monitor_index)
    except Exception as exc:
        logger.warning(
            "Fallo al inicializar captura MSS real (%s). "
            "Activando generador sintético para calibración.",
            exc
        )
        capture_source = FakeCaptureSource()

    # 2. Motor de Visión Matemático SOTA (Invariante al Zoom y Detección de Botones)
    if config.vision_strategy == "geometric_vision_sota":
        vision_strategy = GeometricVisionStrategy(
            button_threshold=config.button_threshold,
            cache_size_enabled=config.cache_button_size
        )
    elif config.vision_strategy == "hsv_contour":
        vision_strategy = HsvContourStrategy()
    elif config.vision_strategy == "sota_template_match":
        vision_strategy = TemplateMatchStrategy(threshold=config.button_threshold)
    else:
        vision_strategy = FakeVisionStrategy()

    # 3. Simulador de Entrada (Ring 0 / Userland / Fake)
    raw_simulator = InputBackendFactory.create(config.input_backend)
    if config.humanized_input:
        input_simulator = HumanizedInputSimulator(raw_simulator, clock)
    else:
        input_simulator = raw_simulator

    # 4. Diagnósticos Visuales No Bloqueantes ('Rayos X') en formato PNG para Flutter/Flet
    diag_sink = QueueDiagnosticsSink(maxsize=2)
    diag_renderer = OpenCVAnnotator(target_size=(640, 480), format="jpeg")

    # 5. Caso de Uso Autónomo: Mover ratón al objetivo y cliquear
    task = FindAndClickTask(click_cooldown_s=0.35)

    # 6. Colas Concurrenciales Hilo-Seguras con Descarte LIFO (Latest-Frame-Wins)
    frame_queue: LatestFrameQueue[Any] = LatestFrameQueue[Any](maxsize=1)
    action_queue: queue.Queue[Any] = queue.Queue(maxsize=10)

    # 7. Pipeline Productor-Consumidor Concurrente
    producer = CaptureProducer(capture_source, frame_queue, clock, target_fps=config.target_fps)
    consumer = VisionConsumer(vision_strategy, frame_queue, action_queue, diag_sink)
    executor = ActionExecutor(action_queue, task, input_simulator, enabled=True)

    supervisor = PipelineSupervisor(producer, consumer, executor)
    runner = ThreadedPipelineRunner(supervisor)

    # 8. Interfaz Gráfica Flet (Flutter Engine para Python)
    app = FletMainApp(
        runner=runner,
        diagnostics=diag_sink,
        renderer=diag_renderer,
        vision_strategy=vision_strategy,
        capture_source=capture_source,
        config=config,
        config_path=config_path
    )
    return app
