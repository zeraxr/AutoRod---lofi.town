import ast
import os
import unittest
from pathlib import Path


class TestArchitectureRules(unittest.TestCase):
    """
    Firewall arquitectónico automatizado. Inspecciona el árbol sintáctico (AST)
    de todo el código fuente para garantizar el cumplimiento de Clean Architecture.
    """

    @classmethod
    def setUpClass(cls) -> None:
        base_dir = Path(__file__).resolve().parent.parent.parent
        cls.src_dir = base_dir / "src" / "autorod"
        assert cls.src_dir.exists(), f"No se encontró el directorio de código: {cls.src_dir}"

    def _get_all_python_files(self, subpackage: str | None = None) -> list[Path]:
        target = self.src_dir / subpackage if subpackage else self.src_dir
        return list(target.rglob("*.py"))

    def _extract_imported_modules(self, file_path: Path) -> set[str]:
        with open(file_path, "r", encoding="utf-8") as f:
            node = ast.parse(f.read(), filename=str(file_path))

        imports = set()
        for item in ast.walk(node):
            if isinstance(item, ast.Import):
                for alias in item.names:
                    imports.add(alias.name.split('.')[0])
            elif isinstance(item, ast.ImportFrom):
                if item.module:
                    imports.add(item.module.split('.')[0])
        return imports

    def test_domain_purity(self) -> None:
        """Verifica que domain/ carezca de librerías de infraestructura y terceros."""
        forbidden = {"cv2", "numpy", "mss", "tkinter", "flet", "ctypes", "pyautogui", "keyboard"}
        domain_files = self._get_all_python_files("domain")

        for file in domain_files:
            imported = self._extract_imported_modules(file)
            violations = imported.intersection(forbidden)
            self.assertEqual(
                violations,
                set(),
                f"Violación de Pureza de Dominio en {file.name}: importó {violations}"
            )

    def test_application_purity(self) -> None:
        """Verifica que application/ no dependa de librerías de UI o hardware directo."""
        forbidden = {"cv2", "mss", "tkinter", "flet", "ctypes", "pyautogui"}
        app_files = self._get_all_python_files("application")

        for file in app_files:
            imported = self._extract_imported_modules(file)
            violations = imported.intersection(forbidden)
            self.assertEqual(
                violations,
                set(),
                f"Violación de Pureza de Aplicación en {file.name}: importó {violations}"
            )

    def test_zero_time_sleep_in_entire_codebase(self) -> None:
        """Verifica la erradicación absoluta de llamadas a time.sleep() en el AST."""
        all_files = self._get_all_python_files()

        for file in all_files:
            with open(file, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename=str(file))

            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Attribute):
                        if node.func.attr == "sleep":
                            if isinstance(node.func.value, ast.Name) and node.func.value.id == "time":
                                self.fail(f"Llamada a time.sleep() detectada en línea {node.lineno} de {file}")

    def test_zero_cv2_imshow_or_waitkey(self) -> None:
        """Verifica que no existan llamadas a ventanas nativas bloqueantes de OpenCV."""
        all_files = self._get_all_python_files()

        for file in all_files:
            with open(file, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename=str(file))

            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                    if isinstance(node.func.value, ast.Name) and node.func.value.id == "cv2":
                        if node.func.attr in ("imshow", "waitKey", "namedWindow", "destroyAllWindows"):
                            self.fail(f"Llamada a cv2.{node.func.attr}() detectada en {file}")

    def test_zero_pyautogui_usage(self) -> None:
        """Verifica que pyautogui esté completamente excluido del proyecto."""
        all_files = self._get_all_python_files()

        for file in all_files:
            imported = self._extract_imported_modules(file)
            self.assertNotIn(
                "pyautogui",
                imported,
                f"Uso ilegal de pyautogui en {file.name}"
            )


if __name__ == "__main__":
    unittest.main()
