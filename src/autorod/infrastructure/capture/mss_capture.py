import time
import ctypes
import numpy as np
import mss
from autorod.domain.ports.capture import ICaptureSource
from autorod.domain.models.image_payload import ImagePayload, PixelFormat
from autorod.domain.errors import CaptureError, ComponentClosedError


class MssCaptureSource(ICaptureSource):
    """
    Adaptador concreto de MSS para captura de fotogramas de alta tasa (Ring 3).
    Habilita DPI awareness en Windows para evitar desalineación de coordenadas
    y 'pantallas negras' en monitores escalados (125%, 150%, 200%).
    Convierte el canal BGRA a BGR y empaqueta los bytes en un ImagePayload inmutable.
    """

    def __init__(
            self,
            monitor_index: int = 1,
            region: dict[str, int] | None = None
    ) -> None:
        self._monitor_index = monitor_index
        self._custom_region = region
        self._sct: mss.MSS | None = None
        self._frame_counter = 0

    @property
    def monitor_index(self) -> int:
        return self._monitor_index

    @property
    def custom_region(self) -> dict[str, int] | None:
        return self._custom_region

    def set_region(self, region: dict[str, int] | None) -> None:
        """Actualiza la región de captura dinámica (ROI)."""
        self._custom_region = region

    def set_monitor(self, monitor_index: int) -> None:
        """Cambia el monitor físico capturado dinámicamente."""
        if self._sct is not None and monitor_index >= len(self._sct.monitors):
            raise CaptureError(
                f"Monitor {monitor_index} no disponible. "
                f"Detectados: {len(self._sct.monitors) - 1} monitores físicos."
            )
        self._monitor_index = monitor_index

    def _enable_dpi_awareness(self) -> None:
        """Fuerza a Windows a reportar píxeles físicos reales."""
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)  # Per-monitor DPI aware
        except Exception:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass

    def start(self) -> None:
        """Inicializa el contexto MSS con DPI físico. Lanza CaptureError en caso de fallo OS."""
        self._enable_dpi_awareness()
        try:
            self._sct = mss.MSS()
            if self._monitor_index >= len(self._sct.monitors):
                raise CaptureError(
                    f"Monitor {self._monitor_index} no disponible. "
                    f"Detectados: {len(self._sct.monitors) - 1} monitores físicos."
                )
        except Exception as exc:
            if isinstance(exc, CaptureError):
                raise
            raise CaptureError(f"Error al inicializar MSS: {exc}") from exc

    def stop(self) -> None:
        """Libera manejadores de dispositivo y contexto subyacente."""
        if self._sct is not None:
            try:
                self._sct.close()
            finally:
                self._sct = None

    def grab(self) -> ImagePayload:
        """
        Captura sincrónicamente la pantalla física, convierte los canales
        BGRA a BGR y entrega un ImagePayload puro e inmutable.
        """
        if self._sct is None:
            raise ComponentClosedError("MssCaptureSource no ha sido inicializado o ya fue cerrado.")

        target = self._custom_region or self._sct.monitors[self._monitor_index]
        try:
            screenshot = self._sct.grab(target)
        except Exception as exc:
            raise CaptureError(f"Fallo en la captura de pantalla física: {exc}") from exc

        self._frame_counter += 1
        return ImagePayload(
            width=screenshot.width,
            height=screenshot.height,
            pixel_format=PixelFormat.BGRA8,
            stride=screenshot.width * 4,
            data=screenshot.raw,
            frame_id=self._frame_counter,
            captured_at_ns=time.monotonic_ns(),
            source_id=f"mss_mon_{self._monitor_index}",
            offset_x=int(target.get("left", 0)),
            offset_y=int(target.get("top", 0))
        )
