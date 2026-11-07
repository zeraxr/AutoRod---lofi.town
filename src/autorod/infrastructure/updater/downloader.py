"""Gestor de descargas de actualizaciones y ejecución de instaladores."""

import os
import sys
import tempfile
import threading
import subprocess
import logging
from pathlib import Path
from typing import Callable
import urllib.request

logger = logging.getLogger(__name__)


class UpdateDownloader:
    """Descarga de forma asíncrona instaladores de nuevas versiones con informe de progreso."""

    def __init__(self) -> None:
        self._cancel_event = threading.Event()
        self._is_downloading = False

    @property
    def is_downloading(self) -> bool:
        return self._is_downloading

    def cancel(self) -> None:
        """Solicita la cancelación de la descarga activa."""
        self._cancel_event.set()

    def download_installer(
        self,
        url: str,
        filename: str = "AutoRod-Setup.exe",
        on_progress: Callable[[float, int, int], None] | None = None,
        on_complete: Callable[[Path], None] | None = None,
        on_error: Callable[[Exception], None] | None = None,
    ) -> None:
        """
        Descarga el archivo del instalador en un hilo desacoplado.
        
        Args:
            url: URL directa del activo (.exe o .zip) del release.
            filename: Nombre con el que se guardará en la carpeta temporal.
            on_progress: Callback (progreso_0_a_1, bytes_descargados, total_bytes).
            on_complete: Callback invocado con la ruta absoluta del archivo descargado.
            on_error: Callback invocado en caso de excepción de red o disco.
        """
        self._cancel_event.clear()
        self._is_downloading = True

        def _worker() -> None:
            dest_dir = Path(tempfile.gettempdir()) / "AutoRodUpdates"
            try:
                dest_dir.mkdir(parents=True, exist_ok=True)
            except Exception:
                pass
            dest_path = dest_dir / filename

            try:
                req = urllib.request.Request(
                    url,
                    headers={
                        "User-Agent": "AutoRod-App-Downloader",
                        "Accept": "application/octet-stream",
                    }
                )
                with urllib.request.urlopen(req, timeout=30.0) as response:
                    total_bytes = int(response.headers.get("Content-Length", 0))
                    downloaded_bytes = 0
                    chunk_size = 64 * 1024  # 64 KB por bloque

                    with open(dest_path, "wb") as f:
                        while not self._cancel_event.is_set():
                            chunk = response.read(chunk_size)
                            if not chunk:
                                break
                            f.write(chunk)
                            downloaded_bytes += len(chunk)
                            if on_progress and total_bytes > 0:
                                progress = min(1.0, downloaded_bytes / total_bytes)
                                on_progress(progress, downloaded_bytes, total_bytes)

                if self._cancel_event.is_set():
                    if dest_path.is_file():
                        try:
                            dest_path.unlink()
                        except Exception:
                            pass
                    logger.info("Descarga de actualización cancelada por el usuario.")
                    return

                self._is_downloading = False
                logger.info("Descarga de actualización completada con éxito: %s (%d bytes)", dest_path, downloaded_bytes)
                if on_complete:
                    on_complete(dest_path)

            except Exception as exc:
                self._is_downloading = False
                logger.error("Error al descargar actualización desde %s: %s", url, exc)
                if on_error:
                    on_error(exc)

        t = threading.Thread(target=_worker, daemon=True, name="AutoRod-InstallerDownloader")
        t.start()

    @staticmethod
    def launch_installer_and_exit(installer_path: Path, on_exit: Callable[[], None] | None = None) -> None:
        """
        Ejecuta el instalador descargado en un proceso desacoplado del árbol de AutoRod
        y cierra la aplicación ordenadamente para permitir que el instalador sobrescriba archivos.
        """
        try:
            logger.info("[UPDATER] Ejecutando instalador oficial: %s", installer_path)
            if sys.platform == "win32":
                detached_flags = 0x00000008 | 0x00000200  # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
                subprocess.Popen(
                    [str(installer_path)],
                    creationflags=detached_flags,
                    close_fds=True
                )
            else:
                subprocess.Popen([str(installer_path)])

            if on_exit:
                on_exit()
        except Exception as exc:
            logger.error("[UPDATER] Fallo al iniciar el proceso del instalador: %s", exc)
            raise
