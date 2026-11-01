import os
import sys
from pathlib import Path
import cv2
import numpy as np

from autorod.domain.ports.templates import ITemplateRepository
from autorod.domain.models.image_payload import ImagePayload, PixelFormat
from autorod.domain.errors import TemplateNotFoundError


class FileTemplateRepository(ITemplateRepository):
    """
    Adaptador concreto para cargar plantillas de botones e interfaz desde el sistema de archivos.
    Mantiene una caché en memoria para garantizar lecturas en O(1) sin I/O en disco durante el ciclo de visión.
    Resuelve de forma robusta la ubicación tanto en desarrollo local como en ejecutables congelados (PyInstaller).
    """

    def __init__(self, base_dir: Path | str | None = None) -> None:
        if base_dir is None:
            candidate = Path(__file__).resolve().parent.parent.parent / "assets" / "templates"
            if not candidate.is_dir() and getattr(sys, "frozen", False):
                # Soporte para ejecutable empaquetado (onefile / onedir)
                meipass = getattr(sys, "_MEIPASS", None)
                if meipass:
                    cand_mei = Path(meipass) / "autorod" / "assets" / "templates"
                    if cand_mei.is_dir():
                        candidate = cand_mei
                if not candidate.is_dir():
                    exe_dir = Path(sys.executable).parent
                    for rel in ("assets/templates", "_internal/autorod/assets/templates", "autorod/assets/templates"):
                        cand_exe = exe_dir / rel
                        if cand_exe.is_dir():
                            candidate = cand_exe
                            break
            self._base_dir = candidate
        else:
            self._base_dir = Path(base_dir).resolve()

        self._cache: dict[str, ImagePayload] = {}

    @property
    def base_dir(self) -> Path:
        return self._base_dir

    def _resolve_path(self, ref_id: str) -> Path:
        """Encuentra la ruta del archivo con o sin extensión .png/.jpg."""
        direct = self._base_dir / ref_id
        if direct.is_file():
            return direct

        with_png = self._base_dir / f"{ref_id}.png"
        if with_png.is_file():
            return with_png

        with_jpg = self._base_dir / f"{ref_id}.jpg"
        if with_jpg.is_file():
            return with_jpg

        return direct

    def has(self, ref_id: str) -> bool:
        """Verifica si el identificador existe en caché o en disco."""
        if ref_id in self._cache:
            return True
        return self._resolve_path(ref_id).is_file()

    def list_templates(self) -> list[str]:
        """Lista los nombres base de todas las plantillas disponibles."""
        if not self._base_dir.is_dir():
            return []
        templates: list[str] = []
        for file in self._base_dir.iterdir():
            if file.is_file() and file.suffix.lower() in (".png", ".jpg", ".jpeg", ".bmp"):
                templates.append(file.stem)
        return sorted(templates)

    def load(self, ref_id: str) -> ImagePayload:
        """
        Extrae de memoria o binario y retorna el recurso visual puro en ImagePayload.
        
        Raises:
            TemplateNotFoundError: Si la plantilla no existe o no pudo ser decodificada.
        """
        clean_key = Path(ref_id).stem
        if clean_key in self._cache:
            return self._cache[clean_key]
        if ref_id in self._cache:
            return self._cache[ref_id]

        file_path = self._resolve_path(ref_id)
        if not file_path.is_file():
            raise TemplateNotFoundError(
                f"Plantilla visual '{ref_id}' no encontrada en '{self._base_dir}'."
            )

        mat = cv2.imread(str(file_path), cv2.IMREAD_COLOR)
        if mat is None:
            raise TemplateNotFoundError(
                f"El archivo '{file_path}' no pudo ser decodificado como imagen OpenCV."
            )

        h, w = mat.shape[:2]
        contiguous_mat = np.ascontiguousarray(mat)
        payload = ImagePayload(
            width=w,
            height=h,
            pixel_format=PixelFormat.BGR8,
            stride=w * 3,
            data=contiguous_mat.tobytes(),
            frame_id=0,
            captured_at_ns=0,
            source_id=f"template_{clean_key}"
        )

        self._cache[clean_key] = payload
        self._cache[ref_id] = payload
        return payload
