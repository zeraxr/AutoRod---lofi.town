from typing import Any
import numpy as np
import cv2
from autorod.domain.models.image_payload import ImagePayload, PixelFormat


def payload_to_ndarray(payload: ImagePayload) -> 'np.ndarray[Any, Any]':
    """
    Convierte el buffer binario agnóstico a matriz BGR estándar de OpenCV.
    Soporta BGR8, BGRA8, RGB8 y GRAY8 de manera robusta.
    """
    arr = np.frombuffer(payload.data, dtype=np.uint8)
    if payload.pixel_format == PixelFormat.BGR8:
        return arr.reshape((payload.height, payload.stride // 3, 3))[:, :payload.width]
    elif payload.pixel_format == PixelFormat.BGRA8:
        bgra = arr.reshape((payload.height, payload.stride // 4, 4))[:, :payload.width]
        return cv2.cvtColor(bgra, cv2.COLOR_BGRA2BGR)
    elif payload.pixel_format == PixelFormat.RGB8:
        rgb = arr.reshape((payload.height, payload.stride // 3, 3))[:, :payload.width]
        return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    elif payload.pixel_format == PixelFormat.GRAY8:
        gray = arr.reshape((payload.height, payload.stride))[:, :payload.width]
        return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    else:
        raise ValueError(f"Formato de píxel no soportado: {payload.pixel_format}")


def payload_to_bgra_or_bgr(payload: ImagePayload) -> tuple['np.ndarray[Any, Any]', 'np.ndarray[Any, Any] | None']:
    """
    Retorna la imagen BGR y la máscara binaria de canal alfa (si existe en formato BGRA8).
    """
    arr = np.frombuffer(payload.data, dtype=np.uint8)
    if payload.pixel_format == PixelFormat.BGRA8:
        bgra = arr.reshape((payload.height, payload.stride // 4, 4))[:, :payload.width]
        bgr = np.ascontiguousarray(bgra[:, :, :3])
        mask = np.ascontiguousarray((bgra[:, :, 3] > 50).astype(np.uint8) * 255)
        return bgr, mask
    bgr = payload_to_ndarray(payload)
    return bgr, None
