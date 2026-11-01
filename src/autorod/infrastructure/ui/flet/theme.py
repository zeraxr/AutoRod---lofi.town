"""Sistema de Diseño y Motor de Temas para AutoRod (Flet).

Proporciona soporte completo para:
- Tokens de diseño inmutables para Flutter/Flet.
- 6 Paletas predefinidas (Default Supabase, Blanco, Rojo, Verde GitHub, Morado, Celeste).
- Verificación matemática de contraste según WCAG 2.2 (Criterios de Éxito 1.4.3 y 1.4.11).
- Patrón Observador reactivo para actualización instantánea de la UI en Flet.
"""

from dataclasses import dataclass
from typing import Callable, Any
import math


@dataclass(frozen=True, slots=True)
class ThemeTokens:
    """Tokens de diseño visual para la interfaz Flet de AutoRod."""
    id: str
    name: str
    primary: str
    primary_hover: str
    primary_active: str
    text_on_primary: str
    glow_color: str
    accent_subtle: str
    border_active: str
    badge_bg: str
    badge_fg: str
    contrast_ratio_on_dark: float
    wcag_compliance: str  # 'AAA', 'AA'


def _hex_to_rgb(hex_code: str) -> tuple[int, int, int]:
    h = hex_code.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _relative_luminance(hex_code: str) -> float:
    r, g, b = _hex_to_rgb(hex_code)
    channels = []
    for c in (r, g, b):
        sc = c / 255.0
        if sc <= 0.04045:
            channels.append(sc / 12.92)
        else:
            channels.append(math.pow((sc + 0.055) / 1.055, 2.4))
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]


def calculate_contrast_ratio(hex1: str, hex2: str) -> float:
    l1 = _relative_luminance(hex1)
    l2 = _relative_luminance(hex2)
    brightest = max(l1, l2)
    darkest = min(l1, l2)
    return round((brightest + 0.05) / (darkest + 0.05), 2)


DARK_BG = "#080809"

THEME_PRESETS: dict[str, ThemeTokens] = {
    "default": ThemeTokens(
        id="default",
        name="Por defecto (Supabase)",
        primary="#3ecf8e",
        primary_hover="#34b27b",
        primary_active="#299764",
        text_on_primary="#080809",
        glow_color="#3ecf8e",
        accent_subtle="#131715",
        border_active="#202b24",
        badge_bg="#141c17",
        badge_fg="#3ecf8e",
        contrast_ratio_on_dark=calculate_contrast_ratio("#3ecf8e", DARK_BG),
        wcag_compliance="AAA"
    ),
    "white": ThemeTokens(
        id="white",
        name="Blanco (Minimalista)",
        primary="#ffffff",
        primary_hover="#f1f5f9",
        primary_active="#e2e8f0",
        text_on_primary="#080809",
        glow_color="#ffffff",
        accent_subtle="#18181b",
        border_active="#2e2e34",
        badge_bg="#222226",
        badge_fg="#f8fafc",
        contrast_ratio_on_dark=calculate_contrast_ratio("#ffffff", DARK_BG),
        wcag_compliance="AAA"
    ),
    "red": ThemeTokens(
        id="red",
        name="Rojo (Cyberpunk Ruby)",
        primary="#ef4444",
        primary_hover="#dc2626",
        primary_active="#b91c1c",
        text_on_primary="#ffffff",
        glow_color="#ef4444",
        accent_subtle="#1a1213",
        border_active="#33181a",
        badge_bg="#221415",
        badge_fg="#f87171",
        contrast_ratio_on_dark=calculate_contrast_ratio("#ef4444", DARK_BG),
        wcag_compliance="AA"
    ),
    "github_green": ThemeTokens(
        id="github_green",
        name="Verde GitHub (Primer)",
        primary="#2ea043",
        primary_hover="#3fb950",
        primary_active="#238636",
        text_on_primary="#ffffff",
        glow_color="#3fb950",
        accent_subtle="#111813",
        border_active="#1b2c1f",
        badge_bg="#131e16",
        badge_fg="#3fb950",
        contrast_ratio_on_dark=calculate_contrast_ratio("#2ea043", DARK_BG),
        wcag_compliance="AA"
    ),
    "purple": ThemeTokens(
        id="purple",
        name="Morado (Neon Violet)",
        primary="#8b5cf6",
        primary_hover="#7c3aed",
        primary_active="#6d28d9",
        text_on_primary="#ffffff",
        glow_color="#a855f7",
        accent_subtle="#17131e",
        border_active="#291e38",
        badge_bg="#1c1626",
        badge_fg="#c084fc",
        contrast_ratio_on_dark=calculate_contrast_ratio("#8b5cf6", DARK_BG),
        wcag_compliance="AA"
    ),
    "cyan": ThemeTokens(
        id="cyan",
        name="Celeste (Electric Sky)",
        primary="#38bdf8",
        primary_hover="#0ea5e9",
        primary_active="#0284c7",
        text_on_primary="#080809",
        glow_color="#38bdf8",
        accent_subtle="#11181e",
        border_active="#182a36",
        badge_bg="#13212b",
        badge_fg="#38bdf8",
        contrast_ratio_on_dark=calculate_contrast_ratio("#38bdf8", DARK_BG),
        wcag_compliance="AAA"
    ),
}


class ThemeManager:
    """Gestor de temas reactivo con patrón observador para Flet."""

    _instance: "ThemeManager | None" = None

    def __init__(self, initial_theme: str = "default") -> None:
        self._current_theme_id = initial_theme if initial_theme in THEME_PRESETS else "default"
        self._listeners: list[Callable[[ThemeTokens], None]] = []

    @classmethod
    def get_instance(cls, initial_theme: str | None = None) -> "ThemeManager":
        if cls._instance is None:
            cls._instance = cls(initial_theme or "default")
        elif initial_theme is not None and initial_theme in THEME_PRESETS:
            cls._instance._current_theme_id = initial_theme
        return cls._instance

    @property
    def current(self) -> ThemeTokens:
        return THEME_PRESETS.get(self._current_theme_id, THEME_PRESETS["default"])

    @property
    def current_id(self) -> str:
        return self._current_theme_id

    def subscribe(self, listener: Callable[[ThemeTokens], None]) -> None:
        if listener not in self._listeners:
            self._listeners.append(listener)
            try:
                listener(self.current)
            except Exception:
                pass

    def unsubscribe(self, listener: Callable[[ThemeTokens], None]) -> None:
        if listener in self._listeners:
            self._listeners.remove(listener)

    def set_theme(self, theme_id: str) -> bool:
        if theme_id not in THEME_PRESETS or theme_id == self._current_theme_id:
            return False

        self._current_theme_id = theme_id
        active_tokens = self.current

        for listener in list(self._listeners):
            try:
                listener(active_tokens)
            except Exception:
                pass
        return True

    def get_all_themes(self) -> list[ThemeTokens]:
        return list(THEME_PRESETS.values())
