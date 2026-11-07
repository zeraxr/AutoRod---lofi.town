import sys
from pathlib import Path

# Compatibilidad de ejecución compilada con Nuitka
if "__compiled__" in globals() and not hasattr(sys, "frozen"):
    sys.frozen = True  # type: ignore[attr-defined]

# Añadir src/ al sys.path para compatibilidad inmediata en PyCharm y consola
src_path = Path(__file__).resolve().parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from autorod.bootstrap import build_app

if __name__ == "__main__":
    app = build_app()
    app.run()
