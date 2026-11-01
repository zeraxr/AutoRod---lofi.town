import unittest
import logging
from pathlib import Path
from autorod.infrastructure.logging.setup import configure_sota_logging


class TestSotaLogging(unittest.TestCase):
    def setUp(self) -> None:
        self.test_log_path = Path("logs/test_autorod.log")
        self._cleanup_handlers()
        if self.test_log_path.exists():
            try:
                self.test_log_path.unlink()
            except Exception:
                pass

    def tearDown(self) -> None:
        self._cleanup_handlers()
        if self.test_log_path.exists():
            try:
                self.test_log_path.unlink()
            except Exception:
                pass

    def _cleanup_handlers(self) -> None:
        root_logger = logging.getLogger("autorod")
        for h in list(root_logger.handlers):
            try:
                h.close()
            except Exception:
                pass
            root_logger.removeHandler(h)

    def test_configure_logging_creates_file_with_header(self) -> None:
        log_path = configure_sota_logging(self.test_log_path)
        self.assertTrue(log_path.exists())

        content = log_path.read_text(encoding="utf-8")
        self.assertIn("AutoRod - Sesión de Ejecución", content)
        self.assertIn("[LOGGING] Sistema de registros SOTA inicializado en:", content)

    def test_logging_overwrites_on_subsequent_runs(self) -> None:
        # Primera ejecución
        configure_sota_logging(self.test_log_path)
        logger = logging.getLogger("autorod")
        logger.info("MENSAJE_SESION_1")

        content1 = self.test_log_path.read_text(encoding="utf-8")
        self.assertIn("MENSAJE_SESION_1", content1)

        # Segunda ejecución (simula reinicio de la aplicación)
        configure_sota_logging(self.test_log_path)
        logger.info("MENSAJE_SESION_2")

        content2 = self.test_log_path.read_text(encoding="utf-8")
        # El contenido de la sesión anterior debe haber sido erradicado
        self.assertNotIn("MENSAJE_SESION_1", content2)
        self.assertIn("MENSAJE_SESION_2", content2)


if __name__ == "__main__":
    unittest.main()
