from dataclasses import dataclass
from typing import Any
from pathlib import Path
import tomllib
import os
import sys


@dataclass(frozen=True, slots=True, kw_only=True)
class AppConfig:
    """Configuración inmutable cargada desde archivo TOML o valores predeterminados (Figma SOTA 1:1)."""
    # 1. Captura y Pantalla (Figma Configuración)
    target_fps: int = 60
    monitor_index: int = 1
    capture_source: str = "mss"                    # 'mss', 'fake'

    # 2. Comportamiento y Accesos Globales (Figma Configuración)
    pause_on_defocus: bool = True                  # Pausar al cambiar de ventana
    minimize_to_tray: bool = True                  # Minimizar a la bandeja del sistema
    open_at_startup: bool = False                  # Abrir al iniciar el sistema
    shortcut_toggle: str = "F8"                    # Iniciar / Pausar global
    shortcut_stop: str = "F9"                      # Detener sesión global

    # 3. Personalización y Tema (Figma Personalización)
    theme_mode: str = "dark"                       # 'dark', 'light', 'system'
    accent_color: str = "#5554d9"                  # Uno de los 6 swatches oficiales
    show_greetings: bool = True                    # Saludos dinámicos en Dashboard
    use_local_time: bool = True                    # Sincronizar saludo según hora del sistema
    enable_transition_animations: bool = True      # Animaciones de transición fluidas
    language: str = "es"                           # 'es', 'en'

    # 4. Parámetros de Detección y Ritmo (Figma Parámetros)
    profile: str = "balanced"                      # 'balanced', 'fast', 'high_precision'
    min_confidence: float = 0.85                   # Confianza mínima (85%)
    color_tolerance: float = 0.20                  # Tolerancia de color (20%)
    search_area: str = "fullscreen"                # 'fullscreen', 'center_50', 'active_area'
    cast_delay_ms: int = 1500                      # Espera entre lanzamientos (1.500 ms)
    max_wait_bite_sec: int = 30                    # Tiempo máximo sin picada (30 s)
    retry_on_lost: bool = True                     # Reintentar si se pierde el objetivo
    pause_on_consecutive_errors: int = 3           # Pausar tras N errores consecutivos

    # 5. Parámetros de Dominio / Motor Legacy (Deprecados de la UI pero preservados para el motor)
    input_backend: str = "sendinput"              # 'interception', 'sendinput', 'postmessage', 'fake'
    vision_strategy: str = "geometric_vision_sota" # 'geometric_vision_sota', 'hsv_contour', 'sota_template_match', 'fake'
    button_threshold: float = 0.63
    cache_button_size: bool = True
    humanized_input: bool = False
    ui_theme: str = "default"                      # Retrocompatibilidad con presets antiguos
    ui_transparency: float = 1.0                   # Deprecado en UI: 1.0 = 100% opaco


def resolve_config_path(path: str = "config.toml") -> Path:
    """Resuelve la ruta del archivo de configuración, soportando modo congelado (PyInstaller)."""
    p = Path(path)
    if getattr(sys, "frozen", False):
        exe_sibling = Path(sys.executable).parent / path
        if exe_sibling.is_file() or not p.is_file():
            return exe_sibling
    if p.is_file():
        return p
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
        monitor_index=int(app_data.get("monitor_index", 1)),
        capture_source=str(app_data.get("capture_source", "mss")),

        pause_on_defocus=bool(app_data.get("pause_on_defocus", True)),
        minimize_to_tray=bool(app_data.get("minimize_to_tray", True)),
        open_at_startup=bool(app_data.get("open_at_startup", False)),
        shortcut_toggle=str(app_data.get("shortcut_toggle", "F8")),
        shortcut_stop=str(app_data.get("shortcut_stop", "F9")),

        theme_mode=str(app_data.get("theme_mode", "dark")),
        accent_color=str(app_data.get("accent_color", "#5554d9")),
        show_greetings=bool(app_data.get("show_greetings", True)),
        use_local_time=bool(app_data.get("use_local_time", True)),
        enable_transition_animations=bool(app_data.get("enable_transition_animations", True)),
        language=str(app_data.get("language", "es")),

        profile=str(app_data.get("profile", "balanced")),
        min_confidence=float(app_data.get("min_confidence", 0.85)),
        color_tolerance=float(app_data.get("color_tolerance", 0.20)),
        search_area=str(app_data.get("search_area", "fullscreen")),
        cast_delay_ms=int(app_data.get("cast_delay_ms", 1500)),
        max_wait_bite_sec=int(app_data.get("max_wait_bite_sec", 30)),
        retry_on_lost=bool(app_data.get("retry_on_lost", True)),
        pause_on_consecutive_errors=int(app_data.get("pause_on_consecutive_errors", 3)),

        input_backend=str(app_data.get("input_backend", "sendinput")),
        vision_strategy=str(app_data.get("vision_strategy", "geometric_vision_sota")),
        button_threshold=float(app_data.get("button_threshold", 0.63)),
        cache_button_size=bool(app_data.get("cache_button_size", True)),
        humanized_input=bool(app_data.get("humanized_input", False)),
        ui_theme=str(app_data.get("ui_theme", "default")),
        ui_transparency=float(app_data.get("ui_transparency", 1.0)),
    )


def save_config(config: AppConfig, path: str = "config.toml") -> None:
    """Persiste la configuración en formato TOML limpio respetando el esquema de AutoRod v2.0."""
    resolved = resolve_config_path(path)
    content = f"""[autorod]
# Captura y Pantalla
target_fps = {config.target_fps}
monitor_index = {config.monitor_index}
capture_source = "{config.capture_source}"

# Comportamiento
pause_on_defocus = {str(config.pause_on_defocus).lower()}
minimize_to_tray = {str(config.minimize_to_tray).lower()}
open_at_startup = {str(config.open_at_startup).lower()}
shortcut_toggle = "{config.shortcut_toggle}"
shortcut_stop = "{config.shortcut_stop}"

# Personalización
theme_mode = "{config.theme_mode}"
accent_color = "{config.accent_color}"
show_greetings = {str(config.show_greetings).lower()}
use_local_time = {str(config.use_local_time).lower()}
enable_transition_animations = {str(config.enable_transition_animations).lower()}
language = "{config.language}"

# Parámetros de Detección y Ritmo
profile = "{config.profile}"
min_confidence = {config.min_confidence:.2f}
color_tolerance = {config.color_tolerance:.2f}
search_area = "{config.search_area}"
cast_delay_ms = {config.cast_delay_ms}
max_wait_bite_sec = {config.max_wait_bite_sec}
retry_on_lost = {str(config.retry_on_lost).lower()}
pause_on_consecutive_errors = {config.pause_on_consecutive_errors}

# Parámetros Internos del Motor
input_backend = "{config.input_backend}"
vision_strategy = "{config.vision_strategy}"
button_threshold = {config.button_threshold:.2f}
cache_button_size = {str(config.cache_button_size).lower()}
humanized_input = {str(config.humanized_input).lower()}
ui_theme = "{config.ui_theme}"
ui_transparency = {config.ui_transparency:.2f}
"""
    with open(resolved, "w", encoding="utf-8") as f:
        f.write(content)
