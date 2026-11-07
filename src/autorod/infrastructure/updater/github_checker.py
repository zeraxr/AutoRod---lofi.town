"""Servicio ligero y asíncrono para comprobación de actualizaciones desde GitHub Releases."""

import re
import json
import logging
import threading
import urllib.request
import urllib.error
from dataclasses import dataclass
from typing import Callable

logger = logging.getLogger(__name__)

CURRENT_VERSION = "2.1.0"
REPO_SLUG = "zeraxr/AutoRod---lofi.town"


@dataclass(frozen=True, slots=True)
class UpdateInfo:
    """Información de la actualización disponible."""
    has_update: bool
    latest_version: str
    current_version: str
    release_name: str
    release_notes: str
    html_url: str
    download_url: str


def _parse_version_tuple(v_str: str) -> tuple[int, ...]:
    """Extrae las componentes numéricas de versiones semánticas (ej. 'v2.1.0' -> (2, 1, 0))."""
    clean = v_str.strip().lstrip("vV")
    numbers = re.findall(r"\d+", clean)
    return tuple(int(n) for n in numbers) if numbers else (0,)


def check_for_updates(
    repo_slug: str = REPO_SLUG,
    current_version: str = CURRENT_VERSION,
    timeout: float = 4.0
) -> UpdateInfo | None:
    """
    Consulta la API pública de GitHub para verificar si existe una nueva versión.
    Falla de forma silenciosa sin interrumpir la ejecución si no hay conexión.
    """
    api_url = f"https://api.github.com/repos/{repo_slug}/releases/latest"
    req = urllib.request.Request(
        api_url,
        headers={
            "User-Agent": f"AutoRod-App/{current_version}",
            "Accept": "application/vnd.github.v3+json",
        }
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            if response.status != 200:
                return None
            data = json.loads(response.read().decode("utf-8"))

        tag_name = data.get("tag_name", "")
        remote_tuple = _parse_version_tuple(tag_name)
        local_tuple = _parse_version_tuple(current_version)

        has_update = remote_tuple > local_tuple

        # Buscar instalador o portable en los assets
        download_url = data.get("html_url", f"https://github.com/{repo_slug}/releases")
        assets = data.get("assets", [])
        for asset in assets:
            name = asset.get("name", "").lower()
            if "setup" in name or ".exe" in name or ".zip" in name:
                download_url = asset.get("browser_download_url", download_url)
                break

        return UpdateInfo(
            has_update=has_update,
            latest_version=tag_name,
            current_version=current_version,
            release_name=data.get("name", tag_name),
            release_notes=data.get("body", "Sin notas de versión disponibles."),
            html_url=data.get("html_url", f"https://github.com/{repo_slug}/releases"),
            download_url=download_url
        )
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, Exception) as exc:
        logger.debug("Comprobación de actualización omitida o sin conexión: %s", exc)
        return None


def run_async_update_check(
    on_update_found: Callable[[UpdateInfo], None],
    current_version: str = CURRENT_VERSION
) -> None:
    """Ejecuta la comprobación en un hilo daemon desacoplado."""
    def _worker() -> None:
        info = check_for_updates(current_version=current_version)
        if info and info.has_update:
            on_update_found(info)

    thread = threading.Thread(target=_worker, daemon=True, name="AutoRod-UpdateChecker")
    thread.start()
