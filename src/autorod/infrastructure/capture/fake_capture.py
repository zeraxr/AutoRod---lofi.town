import math
import time
import cv2
import numpy as np
from autorod.domain.ports.capture import ICaptureSource
from autorod.domain.models.image_payload import ImagePayload, PixelFormat


class FakeCaptureSource(ICaptureSource):
    """
    Adaptador en memoria para tests y modo simulación.
    Genera un patrón de calibración sintético activo (con esfera y dial giratorio)
    para evitar el fallo crítico de 'pantalla negra' durante diagnósticos sin hardware.
    """

    def __init__(self, width: int = 640, height: int = 480) -> None:
        self._width = width
        self._height = height
        self._frame_id = 0
        self._running = False

    def start(self) -> None:
        self._running = True

    def stop(self) -> None:
        self._running = False

    def grab(self) -> ImagePayload:
        self._frame_id += 1
        now_ns = time.monotonic_ns()

        # 1. Crear fondo degradado azul noche para contraste
        img = np.zeros((self._height, self._width, 3), dtype=np.uint8)
        img[:, :] = (35, 25, 20)  # BGR

        # 2. Dibujar rejilla de calibración
        grid_step = 40
        for x in range(0, self._width, grid_step):
            cv2.line(img, (x, 0), (x, self._height), (50, 40, 35), 1)
        for y in range(0, self._height, grid_step):
            cv2.line(img, (0, y), (self._width, y), (50, 40, 35), 1)

        # 3. Dibujar simulación del minijuego circular de pesca (lofi.town)
        center_x, center_y = self._width // 2, self._height // 2
        radius = 90

        # Anillo exterior
        cv2.circle(img, (center_x, center_y), radius, (180, 180, 180), 2)
        # Zona verde objetivo (arco de éxito)
        cv2.ellipse(
            img, (center_x, center_y), (radius, radius),
            0, 30, 90, (0, 230, 80), -1
        )

        # Aguja giratoria animada (invarianza angular)
        angle_rad = (self._frame_id * 8) % 360 * (math.pi / 180.0)
        needle_x = int(center_x + (radius - 10) * math.cos(angle_rad))
        needle_y = int(center_y + (radius - 10) * math.sin(angle_rad))
        cv2.line(img, (center_x, center_y), (needle_x, needle_y), (0, 60, 255), 3)
        cv2.circle(img, (center_x, center_y), 6, (255, 255, 255), -1)

        # 4. Textos de diagnóstico sintético
        cv2.putText(
            img,
            f"CALIBRACION SINTETICA - Fotograma #{self._frame_id}",
            (20, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 255),
            2,
            cv2.LINE_AA
        )
        cv2.putText(
            img,
            "Simulador de Minijuego (lofi.town)",
            (20, self._height - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (200, 200, 200),
            1,
            cv2.LINE_AA
        )

        raw_bytes = img.tobytes()
        return ImagePayload(
            width=self._width,
            height=self._height,
            pixel_format=PixelFormat.BGR8,
            stride=self._width * 3,
            data=raw_bytes,
            frame_id=self._frame_id,
            captured_at_ns=now_ns,
            source_id="synthetic_generator"
        )
