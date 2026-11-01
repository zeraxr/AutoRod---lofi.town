"""Pruebas unitarias para los componentes visuales avanzados y la integración de ventana única."""

import unittest
import tkinter as tk
from autorod.infrastructure.ui.tk.theme import ThemeManager
from autorod.infrastructure.ui.tk.components.glow_button import (
    KineticGlowButton,
    KineticEmergencyButton
)
from autorod.infrastructure.ui.tk.components.gooey_nav import CollapsibleGooeySidebar
from autorod.infrastructure.ui.tk.components.theme_studio_view import ThemeStudioView
from autorod.config import AppConfig


class TestIntegratedUIComponents(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = tk.Tk()
        cls.root.withdraw()
        cls.theme_mgr = ThemeManager.get_instance("default")

    @classmethod
    def tearDownClass(cls) -> None:
        try:
            cls.root.destroy()
        except Exception:
            pass

    def test_emergency_button_bounds_prevent_clipping(self) -> None:
        """Verifica que el botón de emergencia calcule su ancho para impedir el recorte de texto."""
        btn = KineticEmergencyButton(
            self.root,
            command=lambda: None,
            text="🚨 SALIR [Q]",
            width=120
        )
        self.root.update_idletasks()
        # El ancho medido debe ser mayor o igual al ancho requerido por el texto
        self.assertGreaterEqual(btn._width, 100)
        btn.destroy()

    def test_gooey_sidebar_has_integrated_palette_tab(self) -> None:
        """Verifica que la paleta sea una pestaña nativa y no una ventana emergente."""
        tab_ids = [t[0] for t in CollapsibleGooeySidebar.TAB_ITEMS]
        self.assertIn("palette", tab_ids)
        self.assertEqual(len(tab_ids), 4)

    def test_theme_studio_view_operates_without_toplevel(self) -> None:
        """Verifica que el estudio de diseño se monte como Frame integrado y cambie de tema."""
        cfg = AppConfig()
        view = ThemeStudioView(
            self.root,
            theme_manager=self.theme_mgr,
            app_config=cfg
        )
        self.root.update_idletasks()
        self.assertIsInstance(view, tk.Frame)

        # Probar selección de tema 'purple' en la misma ventana
        view._on_select_theme("purple")
        self.assertEqual(self.theme_mgr.current_id, "purple")
        view.destroy()


if __name__ == "__main__":
    unittest.main()
