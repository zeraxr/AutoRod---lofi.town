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
    scan_region_enabled: bool = True               # Habilitar zona de escaneo recortada
    scan_x1: int = 670
    scan_y1: int = 246
    scan_x2: int = 1244
    scan_y2: int = 700

    # 2. Comportamiento y Accesos Globales (Figma Configuración)
    pause_on_defocus: bool = True                  # Pausar al cambiar de ventana
    minimize_to_tray: bool = True                  # Minimizar a la bandeja del sistema
    open_at_startup: bool = False                  # Abrir al iniciar el sistema
    shortcut_toggle: str = "Shift+Q"                    # Iniciar / Pausar global
    shortcut_stop: str = "Alt+Q"                      # Detener sesión global

    # 3. Personalización y Tema (Figma Personalización)
    theme_mode: str = "dark"                       # 'dark', 'light', 'system'
    accent_color: str = "#5554d9"                  # Uno de los 6 swatches oficiales
    show_greetings: bool = True                    # Saludos dinámicos en Dashboard
    use_local_time: bool = True                    # Sincronizar saludo según hora del sistema
    enable_transition_animations: bool = True      # Animaciones de transición fluidas
    language: str = "es"                           # 'es', 'en'

    # 4. Parámetros de Dominio / Motor (Invariantes internas calibradas)
    input_backend: str = "sendinput"              # 'interception', 'sendinput', 'postmessage', 'fake'
    vision_strategy: str = "geometric_vision_sota" # 'geometric_vision_sota', 'hsv_contour', 'sota_template_match', 'fake'
    button_threshold: float = 0.63
    cache_button_size: bool = True
    required_cycles_to_lock: int = 5              # Ciclos exitosos necesarios para fijar el caché
    cache_inactivity_timeout_s: float = 90.0      # Ventana de inactividad máxima en caché bloqueado
    humanized_input: bool = False
    ui_theme: str = "default"                      # Retrocompatibilidad con presets antiguos
    ui_transparency: float = 1.0                   # 1.0 = 100% opaco

    def get_scan_region(self) -> dict[str, int] | None:
        """Calcula el diccionario de región para MSS si scan_region_enabled es True."""
        if not self.scan_region_enabled:
            return None
        left = min(self.scan_x1, self.scan_x2)
        top = min(self.scan_y1, self.scan_y2)
        width = abs(self.scan_x2 - self.scan_x1)
        height = abs(self.scan_y2 - self.scan_y1)
        if width <= 0 or height <= 0:
            return None
        return {"top": top, "left": left, "width": width, "height": height}


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
        scan_region_enabled=bool(app_data.get("scan_region_enabled", True)),
        scan_x1=int(app_data.get("scan_x1", 670)),
        scan_y1=int(app_data.get("scan_y1", 246)),
        scan_x2=int(app_data.get("scan_x2", 1244)),
        scan_y2=int(app_data.get("scan_y2", 700)),

        pause_on_defocus=bool(app_data.get("pause_on_defocus", True)),
        minimize_to_tray=bool(app_data.get("minimize_to_tray", True)),
        open_at_startup=bool(app_data.get("open_at_startup", False)),
        shortcut_toggle=str(app_data.get("shortcut_toggle", "Shift+Q")),
        shortcut_stop=str(app_data.get("shortcut_stop", "Alt+Q")),

        theme_mode=str(app_data.get("theme_mode", "dark")),
        accent_color=str(app_data.get("accent_color", "#5554d9")),
        show_greetings=bool(app_data.get("show_greetings", True)),
        use_local_time=bool(app_data.get("use_local_time", True)),
        enable_transition_animations=bool(app_data.get("enable_transition_animations", True)),
        language=str(app_data.get("language", "es")),

        input_backend=str(app_data.get("input_backend", "sendinput")),
        vision_strategy=str(app_data.get("vision_strategy", "geometric_vision_sota")),
        button_threshold=float(app_data.get("button_threshold", 0.63)),
        cache_button_size=bool(app_data.get("cache_button_size", True)),
        required_cycles_to_lock=int(app_data.get("required_cycles_to_lock", 5)),
        cache_inactivity_timeout_s=float(app_data.get("cache_inactivity_timeout_s", 90.0)),
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
scan_region_enabled = {str(config.scan_region_enabled).lower()}
scan_x1 = {config.scan_x1}
scan_y1 = {config.scan_y1}
scan_x2 = {config.scan_x2}
scan_y2 = {config.scan_y2}

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

# Parámetros Internos del Motor
input_backend = "{config.input_backend}"
vision_strategy = "{config.vision_strategy}"
button_threshold = {config.button_threshold:.2f}
cache_button_size = {str(config.cache_button_size).lower()}
required_cycles_to_lock = {config.required_cycles_to_lock}
cache_inactivity_timeout_s = {config.cache_inactivity_timeout_s:.1f}
humanized_input = {str(config.humanized_input).lower()}
ui_theme = "{config.ui_theme}"
ui_transparency = {config.ui_transparency:.2f}
"""
    with open(resolved, "w", encoding="utf-8") as f:
        f.write(content)
