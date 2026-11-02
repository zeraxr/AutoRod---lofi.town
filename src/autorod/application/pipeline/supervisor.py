import threading
import logging
from types import TracebackType
from typing import Any
from autorod.application.pipeline.producer import CaptureProducer
from autorod.application.pipeline.consumer import VisionConsumer
from autorod.application.pipeline.executor import ActionExecutor

logger = logging.getLogger(__name__)


class PipelineSupervisor:
    """
    Orquestador del ciclo de vida estricto de los hilos de trabajo.
    Garantiza apagado ordenado sin demonios huérfanos.
    """

    def __init__(
            self,
            producer: CaptureProducer,
            consumer: VisionConsumer,
            executor: ActionExecutor
    ) -> None:
        self._producer = producer
        self._consumer = consumer
        self._executor = executor
        self._threads: list[threading.Thread] = []

    @property
    def producer(self) -> CaptureProducer:
        return self._producer

    @property
    def consumer(self) -> VisionConsumer:
        return self._consumer

    @property
    def executor(self) -> ActionExecutor:
        return self._executor

    def __enter__(self) -> 'PipelineSupervisor':
        self.start()
        return self

    def __exit__(
            self,
            exc_type: type[BaseException] | None,
            exc_val: BaseException | None,
            exc_tb: TracebackType | None
    ) -> None:
        self.stop()
        self.join()

    def start(self) -> None:
        if self._threads:
            raise RuntimeError("Pipeline ya está en ejecución.")

        self._threads = [
            threading.Thread(target=self._producer.run, name="Th-Producer", daemon=True),
            threading.Thread(target=self._consumer.run, name="Th-Vision", daemon=True),
            threading.Thread(target=self._executor.run, name="Th-Executor", daemon=True)
        ]

        for t in self._threads:
            t.start()
        logger.info("Pipeline SOTA iniciado. Hilos desplegados.")

    def stop(self) -> None:
        logger.info("Inyectando señales de parada cooperativa...")
        self._producer.stop()

    def join(self, timeout_s: float = 3.0) -> None:
        for t in self._threads:
            t.join(timeout=timeout_s)
            if t.is_alive():
                logger.error(f"Fuga detectada: Hilo {t.name} no respondió al Sentinel.")
        self._threads.clear()
        logger.info("Pipeline colapsado de forma segura.")
