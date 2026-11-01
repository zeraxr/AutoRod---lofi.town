import os
import sys
import logging
from pathlib import Path
from datetime import datetime


class AutoFlushFileHandler(logging.FileHandler):
    """FileHandler que fuerza el flush inmediato a disco en cada registro emitido.
    
    Garantiza que el archivo de log en disco esté 100% sincronizado en tiempo real
    para auditorías instantáneas del modelo de IA o del desarrollador.
    """

    def emit(self, record: logging.LogRecord) -> None:
        super().emit(record)
        self.flush()


def configure_sota_logging(
    log_file_path: str | Path = "logs/autorod.log",
    log_level: int = logging.INFO
) -> Path:
    """Configura el sistema de registro industrial SOTA para AutoRod.
    
    Características clave:
      - Archivo único en 'logs/autorod.log' con modo de apertura 'w' (sobrescribe en cada inicio).
      - Elimina la acumulación de archivos residuales o basura histórica.
      - Sincronización inmediata (auto-flush) en disco.
      - Estructura temporal micro-precisa (milisegundos) y trazabilidad por componente.
      - Compatible con la consola interactiva y con la vista de telemetría de Flet.
    
    Returns:
        Path absoluto del archivo de registro activo.
    """
    resolved_path = Path(log_file_path).resolve()
    resolved_path.parent.mkdir(parents=True, exist_ok=True)

    root_logger = logging.getLogger("autorod")
    root_logger.setLevel(log_level)

    # 1. Cerrar y remover handlers existentes para liberar descriptores de archivo en Windows
    for existing in list(root_logger.handlers):
        if isinstance(existing, (logging.FileHandler, logging.StreamHandler)):
            try:
                existing.close()
            except Exception:
                pass
            root_logger.removeHandler(existing)

    # 2. Formateador SOTA de alta fidelidad
    formatter = logging.Formatter(
        fmt="%(asctime)s.%(msecs)03d [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # 3. Handler de archivo con modo 'w' que trunca y limpia el archivo inmediatamente
    file_handler = AutoFlushFileHandler(resolved_path, mode="w", encoding="utf-8")
    file_handler.setFormatter(formatter)
    file_handler.setLevel(log_level)

    # 4. Escribir cabecera visual de sesión limpia en el stream del archivo
    sep = "=" * 80
    header = (
        f"{sep}\n"
        f"AutoRod SOTA v2.0 - Sesión de Ejecución\n"
        f"Fecha y Hora de Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"Python: {sys.version.split()[0]} | Plataforma: {sys.platform}\n"
        f"UI Engine: Flet Desktop (Flutter Engine para Python)\n"
        f"{sep}\n"
    )
    if file_handler.stream:
        file_handler.stream.write(header)
        file_handler.flush()

    # 5. Handler de consola para terminal / IDE
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)

    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    root_logger.info("[LOGGING] Sistema de registros SOTA inicializado en: %s", resolved_path)
    return resolved_path
