import unittest
import sys
import tempfile
from pathlib import Path
from autorod.config import AppConfig, resolve_config_path, load_config, save_config


class TestAppConfig(unittest.TestCase):
    def test_default_config_properties(self) -> None:
        cfg = AppConfig()
        self.assertEqual(cfg.target_fps, 60)
        self.assertEqual(cfg.input_backend, "sendinput")
        self.assertEqual(cfg.vision_strategy, "geometric_vision_sota")
        self.assertTrue(cfg.cache_button_size)

    def test_resolve_config_path_development(self) -> None:
        p = resolve_config_path("config.toml")
        self.assertIsInstance(p, Path)

    def test_resolve_config_path_frozen_mode(self) -> None:
        original_frozen = getattr(sys, "frozen", False)
        original_executable = sys.executable
        try:
            sys.frozen = True  # type: ignore[attr-defined]
            sys.executable = str(Path(tempfile.gettempdir()) / "AutoRod" / "AutoRod.exe")
            expected_sibling = Path(sys.executable).parent / "config.toml"

            # Cuando no existe en cwd (un path ficticio inexistente)
            resolved = resolve_config_path("non_existent_relative_cfg.toml")
            self.assertEqual(resolved, Path(sys.executable).parent / "non_existent_relative_cfg.toml")
        finally:
            if original_frozen:
                sys.frozen = original_frozen  # type: ignore[attr-defined]
            else:
                delattr(sys, "frozen")
            sys.executable = original_executable

    def test_load_and_save_config_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            cfg_path = Path(tmpdir) / "test_config.toml"
            cfg = AppConfig(
                target_fps=75,
                input_backend="win32",
                vision_strategy="hsv_contours",
                ui_theme="github_green",
                ui_transparency=0.92
            )
            save_config(cfg, str(cfg_path))
            self.assertTrue(cfg_path.is_file())

            loaded = load_config(str(cfg_path))
            self.assertEqual(loaded.target_fps, 75)
            self.assertEqual(loaded.input_backend, "win32")
            self.assertEqual(loaded.vision_strategy, "hsv_contours")
            self.assertEqual(loaded.ui_theme, "github_green")
            self.assertAlmostEqual(loaded.ui_transparency, 0.92)


if __name__ == "__main__":
    unittest.main()
