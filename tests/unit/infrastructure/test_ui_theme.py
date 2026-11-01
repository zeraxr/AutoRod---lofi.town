"""Pruebas unitarias para el motor de temas y tokens WCAG 2.2 de AutoRod."""

import unittest
from autorod.infrastructure.ui.flet.theme import (
    ThemeManager,
    THEME_PRESETS,
    calculate_contrast_ratio,
    _relative_luminance
)
from autorod.config import AppConfig, save_config, load_config
import tempfile
import os


class TestThemeEngine(unittest.TestCase):
    def setUp(self) -> None:
        self.mgr = ThemeManager("default")

    def test_all_six_required_themes_exist(self) -> None:
        """Verifica que los 6 temas solicitados estén definidos formalmente."""
        required_keys = {"default", "white", "red", "github_green", "purple", "cyan"}
        self.assertTrue(required_keys.issubset(set(THEME_PRESETS.keys())))

    def test_wcag_contrast_ratios_meet_standards(self) -> None:
        """Comprueba que todos los temas cumplan al menos WCAG 2.2 Nivel AA (>= 4.5:1)."""
        dark_bg = "#0c0d10"
        for tid, tokens in THEME_PRESETS.items():
            ratio = calculate_contrast_ratio(tokens.primary, dark_bg)
            self.assertGreaterEqual(
                ratio,
                4.5,
                f"El tema '{tid}' ({tokens.primary}) no cumple el ratio mínimo de 4.5:1 contra {dark_bg}"
            )
            self.assertIn(tokens.wcag_compliance, ("AA", "AAA"))

    def test_theme_manager_subscription(self) -> None:
        """Verifica el patrón observador al cambiar de tema."""
        received_tokens = []
        self.mgr.subscribe(lambda t: received_tokens.append(t.id))

        # Al suscribirse recibe el actual ("default")
        self.assertEqual(received_tokens, ["default"])

        # Cambiar a 'purple'
        success = self.mgr.set_theme("purple")
        self.assertTrue(success)
        self.assertEqual(self.mgr.current_id, "purple")
        self.assertEqual(received_tokens, ["default", "purple"])

    def test_theme_config_serialization(self) -> None:
        """Verifica que el tema y la transparencia se guarden y lean de config.toml."""
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".toml") as tmp:
            tmp_path = tmp.name

        try:
            cfg = AppConfig(ui_theme="cyan", ui_transparency=0.92)
            save_config(cfg, tmp_path)

            loaded = load_config(tmp_path)
            self.assertEqual(loaded.ui_theme, "cyan")
            self.assertAlmostEqual(loaded.ui_transparency, 0.92)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)


if __name__ == "__main__":
    unittest.main()
