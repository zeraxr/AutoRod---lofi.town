import cv2
from autorod.domain.ports.diagnostics import IDiagnosticsRenderer
from autorod.domain.models.diagnostics import DiagnosticFrame
from autorod.infrastructure.imaging.numpy_bridge import payload_to_ndarray


class OpenCVAnnotator(IDiagnosticsRenderer):
    """
    Renderizador SOTA de diagnósticos visuales ('Rayos X').
    Dibuja metadatos, regiones de interés (ROI) y HUD sobre la imagen,
    escalando adaptativamente para ajustarse a la UI sin pérdida
    de proporciones ni bloqueos de concurrencia.
    """

    def __init__(self, target_size: tuple[int, int] = (640, 480), format: str = "png") -> None:
        self._target_width, self._target_height = target_size
        self._format = format.lower().lstrip(".")

    def render(self, frame: DiagnosticFrame) -> bytes:
        # 1. Recuperar matriz BGR desde el ImagePayload puro
        img = payload_to_ndarray(frame.payload).copy()
        orig_h, orig_w = img.shape[:2]

        # 2. Calcular factor de escala para ajuste perfecto al Canvas / Image
        scale = min(self._target_width / orig_w, self._target_height / orig_h)
        new_w = max(1, int(orig_w * scale))
        new_h = max(1, int(orig_h * scale))

        # Redimensionar para rendimiento óptimo en la UI
        scaled_img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)

        # 3. Dibujar bounding boxes escalados proporcionalmente
        ox = getattr(frame.payload, "offset_x", 0)
        oy = getattr(frame.payload, "offset_y", 0)
        for bbox in frame.bounding_boxes:
            local_x = bbox.top_left.x - ox
            local_y = bbox.top_left.y - oy
            pt1 = (int(local_x * scale), int(local_y * scale))
            pt2 = (
                int((local_x + bbox.size.width) * scale),
                int((local_y + bbox.size.height) * scale)
            )
            # Rectángulo verde neón de alta visibilidad
            cv2.rectangle(scaled_img, pt1, pt2, (0, 255, 128), 2)

        # 4. Dibujar HUD informativo ('Rayos X')
        hud_header = f"Rayos X: {frame.layer_name}"
        cv2.putText(
            scaled_img,
            hud_header,
            (10, 25),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 255),
            2,
            cv2.LINE_AA
        )

        y_offset = 50
        for label in frame.labels:
            cv2.putText(
                scaled_img,
                label,
                (10, y_offset),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 0),
                1,
                cv2.LINE_AA
            )
            y_offset += 20

        # 5. Codificar en buffer binario (PNG nativo de Flutter/Flet o PPM)
        ext = f".{self._format}"
        success, buffer = cv2.imencode(ext, scaled_img)
        if not success:
            raise RuntimeError(f"Fallo crítico al codificar fotograma a formato {self._format}.")

        return buffer.tobytes()
