"""Pruebas unitarias para el comprobador de versiones semánticas, detección de entorno y diálogos."""

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from autorod.infrastructure.updater.github_checker import (
    _parse_version_tuple,
    UpdateInfo,
    CURRENT_VERSION
)
from autorod.infrastructure.updater.detector import (
    detect_installation_type,
    is_installed_setup,
    InstallationType
)
from autorod.infrastructure.ui.flet.components.update_dialog import FletUpdateHintDialog
from autorod.infrastructure.ui.flet.components.title_bar import FletCustomTitleBar


class TestUpdateChecker(unittest.TestCase):

    def test_parse_version_tuple(self) -> None:
        self.assertEqual(_parse_version_tuple("v2.0.0"), (2, 0, 0))
        self.assertEqual(_parse_version_tuple("2.1.5"), (2, 1, 5))
        self.assertEqual(_parse_version_tuple("v3.0.0-rc1"), (3, 0, 0, 1))

    def test_semver_comparisons(self) -> None:
        v_current = _parse_version_tuple("2.0.0")
        v_newer = _parse_version_tuple("v2.1.0")
        v_older = _parse_version_tuple("v1.9.9")
        v_equal = _parse_version_tuple("2.0.0")

        self.assertGreater(v_newer, v_current)
        self.assertLess(v_older, v_current)
        self.assertEqual(v_equal, v_current)

    def test_update_info_dataclass(self) -> None:
        info = UpdateInfo(
            has_update=True,
            latest_version="v2.1.0",
            current_version="2.0.0",
            release_name="AutoRod v2.1.0",
            release_notes="Mejoras visuales",
            html_url="https://github.com/zeraxr/AutoRod/releases/v2.1.0",
            download_url="https://github.com/zeraxr/AutoRod/releases/download/v2.1.0/Setup.exe",
            setup_download_url="https://github.com/zeraxr/AutoRod/releases/download/v2.1.0/Setup.exe",
            portable_download_url="https://github.com/zeraxr/AutoRod/releases/download/v2.1.0/Portable.zip",
            asset_name="AutoRod-Setup.exe",
            asset_size_bytes=52428800
        )
        self.assertTrue(info.has_update)
        self.assertEqual(info.latest_version, "v2.1.0")
        self.assertEqual(info.setup_download_url, "https://github.com/zeraxr/AutoRod/releases/download/v2.1.0/Setup.exe")

    def test_detect_installation_type_override(self) -> None:
        """Verifica que la variable de entorno permita emular todos los tipos de instalación."""
        orig = os.environ.get("AUTOROD_FORCE_INSTALL_TYPE")
        try:
            os.environ["AUTOROD_FORCE_INSTALL_TYPE"] = "portable"
            self.assertEqual(detect_installation_type(), InstallationType.PORTABLE)
            self.assertFalse(is_installed_setup())

            os.environ["AUTOROD_FORCE_INSTALL_TYPE"] = "installed"
            self.assertEqual(detect_installation_type(), InstallationType.INSTALLED)
            self.assertTrue(is_installed_setup())

            os.environ["AUTOROD_FORCE_INSTALL_TYPE"] = "development"
            self.assertEqual(detect_installation_type(), InstallationType.DEVELOPMENT)
            self.assertFalse(is_installed_setup())
        finally:
            if orig is not None:
                os.environ["AUTOROD_FORCE_INSTALL_TYPE"] = orig
            else:
                os.environ.pop("AUTOROD_FORCE_INSTALL_TYPE", None)

    def test_title_bar_blue_dot_behavior(self) -> None:
        """Verifica que el punto azul esté apagado por defecto y solo se encienda con nueva versión."""
        tb = FletCustomTitleBar(page=None, on_close=lambda: None)
        # 1. Por defecto apagado
        self.assertFalse(tb._update_dot.visible)

        # 2. Si no hay actualización (has_update=False), debe permanecer apagado
        no_update = UpdateInfo(
            has_update=False,
            latest_version="v2.1.0",
            current_version="2.1.0",
            release_name="v2.1.0",
            release_notes="",
            html_url="",
            download_url=""
        )
        tb.set_update_available(no_update)
        self.assertFalse(tb._update_dot.visible)

        # 3. Si hay actualización (has_update=True), debe encenderse
        update_avail = UpdateInfo(
            has_update=True,
            latest_version="v2.2.0",
            current_version="2.1.0",
            release_name="v2.2.0",
            release_notes="Nueva versión disponible",
            html_url="https://github.com/zeraxr/AutoRod/releases",
            download_url="https://github.com/zeraxr/AutoRod/releases/download/Setup.exe"
        )
        tb.set_update_available(update_avail)
        self.assertTrue(tb._update_dot.visible)

    def test_update_hint_dialog_portable_workflow(self) -> None:
        """Verifica que en versión Portable muestre el mensaje obligatorio para abrir el repositorio."""
        orig = os.environ.get("AUTOROD_FORCE_INSTALL_TYPE")
        try:
            os.environ["AUTOROD_FORCE_INSTALL_TYPE"] = "portable"

            mock_page = MagicMock()
            dialog = FletUpdateHintDialog(page=mock_page)

            info = UpdateInfo(
                has_update=True,
                latest_version="v2.2.0",
                current_version="2.1.0",
                release_name="AutoRod 2.2",
                release_notes="Notas de la versión",
                html_url="https://github.com/zeraxr/AutoRod---lofi.town/releases",
                download_url=""
            )
            dialog.show(preloaded_info=info)

            # Verificar que la instrucción obligatoria esté presente en los controles del cuerpo
            found_instruction = False
            for ctrl in dialog._body_column.controls:
                val = getattr(ctrl, "value", "")
                if "Se ha encontrado una nueva versión, haz click para abrir el repositorio" in str(val):
                    found_instruction = True
                    break

            self.assertTrue(found_instruction)

            # Verificar botón de Abrir Repositorio en las acciones
            action_texts = [
                str(getattr(c.content.controls[-1], "value", ""))
                for c in dialog._actions_row.controls
                if hasattr(c, "content") and hasattr(c.content, "controls")
            ]
            self.assertIn("Abrir Repositorio", action_texts)
        finally:
            if orig is not None:
                os.environ["AUTOROD_FORCE_INSTALL_TYPE"] = orig
            else:
                os.environ.pop("AUTOROD_FORCE_INSTALL_TYPE", None)

    def test_update_hint_dialog_installed_workflow(self) -> None:
        """Verifica que en versión Instalada por Setup ofrezca actualizar automáticamente."""
        orig = os.environ.get("AUTOROD_FORCE_INSTALL_TYPE")
        try:
            os.environ["AUTOROD_FORCE_INSTALL_TYPE"] = "installed"

            mock_page = MagicMock()
            dialog = FletUpdateHintDialog(page=mock_page)

            info = UpdateInfo(
                has_update=True,
                latest_version="v2.2.0",
                current_version="2.1.0",
                release_name="AutoRod 2.2",
                release_notes="Notas de la versión",
                html_url="https://github.com/zeraxr/AutoRod---lofi.town/releases",
                download_url="https://github.com/zeraxr/AutoRod---lofi.town/releases/download/AutoRod-Setup.exe"
            )
            dialog.show(preloaded_info=info)

            # Verificar botón de Actualizar Ahora en las acciones
            action_texts = [
                str(getattr(c.content.controls[-1], "value", ""))
                for c in dialog._actions_row.controls
                if hasattr(c, "content") and hasattr(c.content, "controls")
            ]
            self.assertIn("Actualizar Ahora", action_texts)
        finally:
            if orig is not None:
                os.environ["AUTOROD_FORCE_INSTALL_TYPE"] = orig
            else:
                os.environ.pop("AUTOROD_FORCE_INSTALL_TYPE", None)

    def test_update_hint_dialog_up_to_date_workflow(self) -> None:
        """Verifica la vista de que el software se encuentra al día."""
        mock_page = MagicMock()
        dialog = FletUpdateHintDialog(page=mock_page)

        info = UpdateInfo(
            has_update=False,
            latest_version="v2.1.0",
            current_version="2.1.0",
            release_name="AutoRod 2.1.0",
            release_notes="",
            html_url="",
            download_url=""
        )
        dialog.show(preloaded_info=info)

        # Debe mostrar "¡AutoRod está actualizado!"
        first_row = dialog._body_column.controls[0]
        title_text = first_row.controls[1].controls[0].value
        self.assertIn("AutoRod está actualizado", title_text)


if __name__ == "__main__":
    unittest.main()
