from dataclasses import dataclass
from typing import Any
from pathlib import Path
import tomllib
import os
import sys


@dataclass(frozen=True, slots=True, kw_only=True)
class AppConfig:
    """Configuración inmutable cargada desde archivo TOML o valores predeterminados."""
    target_fps: int = 60
    input_backend: str = "sendinput"              # 'interception', 'sendinput', 'fake'
    vision_strategy: str = "geometric_vision_sota" # 'geometric_vision_sota', 'hsv_contour', 'sota_template_match', 'fake'
    capture_source: str = "mss"                    # 'mss', 'fake'
    monitor_index: int = 1
    button_threshold: float = 0.63
    cache_button_size: bool = True
    humanized_input: bool = False
    ui_theme: str = "default"                      # 'default', 'white', 'red', 'github_green', 'purple', 'cyan'
    ui_transparency: float = 0.96                  # 0.5 a 1.0 (opacidad de la ventana)


def resolve_config_path(path: str = "config.toml") -> Path:
    """Resuelve la ruta del archivo de configuración, soportando modo congelado (PyInstaller)."""
    p = Path(path)
    if p.is_file():
        return p
    if getattr(sys, "frozen", False):
        exe_sibling = Path(sys.executable).parent / path
        if exe_sibling.is_file():
            return exe_sibling
    return p


def load_config(path: str = "config.toml") -> AppConfig:
    """Lee la configuración y devuelve el objeto de dominio inmutable."""
    resolved = resolve_config_path(path)
    if not resolved.exists():
        return AppConfig()

    with open(resolved, "rb") as f:
        data = tomllib.load(f)

    app_data: dict[str, Any] = data.get("autorod", {})
    return AppConfig(
        target_fps=int(app_data.get("target_fps", 60)),
        input_backend=str(app_data.get("input_backend", "sendinput")),
        vision_strategy=str(app_data.get("vision_strategy", "geometric_vision_sota")),
        capture_source=str(app_data.get("capture_source", "mss")),
        monitor_index=int(app_data.get("monitor_index", 1)),
        button_threshold=float(app_data.get("button_threshold", 0.63)),
        cache_button_size=bool(app_data.get("cache_button_size", True)),
        humanized_input=bool(app_data.get("humanized_input", False)),
        ui_theme=str(app_data.get("ui_theme", "default")),
        ui_transparency=float(app_data.get("ui_transparency", 0.96)),
    )


def save_config(config: AppConfig, path: str = "config.toml") -> None:
    """Persiste la configuración en formato TOML limpio."""
    resolved = resolve_config_path(path)
    content = f"""[autorod]
target_fps = {config.target_fps}
input_backend = "{config.input_backend}"
vision_strategy = "{config.vision_strategy}"
capture_source = "{config.capture_source}"
monitor_index = {config.monitor_index}
button_threshold = {config.button_threshold:.2f}
cache_button_size = {str(config.cache_button_size).lower()}
humanized_input = {str(config.humanized_input).lower()}
ui_theme = "{config.ui_theme}"
ui_transparency = {config.ui_transparency:.2f}
"""
    with open(resolved, "w", encoding="utf-8") as f:
        f.write(content)
