import queue
import logging
from typing import Any
from autorod.domain.ports.vision import IVisionStrategy
from autorod.domain.ports.diagnostics import IDiagnosticsSink
from autorod.domain.models.diagnostics import DiagnosticFrame
from autorod.application.pipeline.queues import LatestFrameQueue, _STOP

logger = logging.getLogger(__name__)


class VisionConsumer:
    """Procesa fotogramas agnósticos y encola deducciones matemáticas."""

    def __init__(
            self,
            strategy: IVisionStrategy,
            frame_queue: LatestFrameQueue[Any],
            action_queue: queue.Queue[Any],
            diagnostics: IDiagnosticsSink,
    ) -> None:
        self._strategy = strategy
        self._frame_queue = frame_queue
        self._action_queue = action_queue
        self._diagnostics = diagnostics
        self._last_status = ""

    def run(self) -> None:
        while True:
            item = self._frame_queue.get()
            if item is _STOP:
                self._action_queue.put(_STOP)
                self._frame_queue.task_done()
                break

            result = self._strategy.analyze(item)

            # Publicación de Rayos X con telemetría de HUD
            status_text = "RASTREANDO..."
            if result.found:
                if result.strategy_id == "cast_button_detected":
                    status_text = "BOTON 'CAST!' DETECTADO"
                elif result.strategy_id == "reel_button_detected":
                    status_text = "BOTON 'REEL!' DETECTADO"
                elif result.strategy_id == "minigame_needle_hit":
                    status_text = "MINIJUEGO: IMPACTO DE AGUJA"
                elif result.strategy_id == "blank_card_detected":
                    status_text = "TARJETA DE PEZ DETECTADA (SALTANDO)"
                else:
                    status_text = f"OBJETIVO: {result.strategy_id.upper()}"
            elif result.strategy_id == "minigame_tracking":
                status_text = "MINIJUEGO: ESPERANDO AGUJA..."

            if status_text != self._last_status:
                if status_text != "RASTREANDO...":
                    logger.info("[VISION] %s (Confianza: %.1f%%)", status_text, result.confidence * 100)
                self._last_status = status_text

            diag = DiagnosticFrame(
                payload=item,
                layer_name=self._strategy.strategy_id,
                bounding_boxes=[result.region] if result.region else [],
                labels=[
                    f"Estado: {status_text}",
                    f"Confianza: {result.confidence * 100:.1f}%",
                    f"Fotograma: #{item.frame_id}"
                ]
            )
            self._diagnostics.publish(diag)

            if result.found:
                self._action_queue.put(result)

            self._frame_queue.task_done()
