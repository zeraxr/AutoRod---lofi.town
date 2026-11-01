# Arquitectura de AutoRod

## 1. Clean Architecture (Ports & Adapters)
- **Domain**: Contiene lógica matemática pura, tipos inmutables (`ImagePayload`) y puertos (`IVisionStrategy`).
- **Application**: Orquesta el caso de uso aislando las dependencias a través de un Pipeline estricto Productor-Consumidor acoplado por `queue.Queue`.
- **Infrastructure**: Implementaciones reales que tocan el hardware (OpenCV, Flet, ctypes, mss).

## 2. Inyección de Dependencias
Todo acoplamiento a librerías concretas se retrasa hasta la *Composition Root* (`bootstrap.py`). El dominio ignora la existencia de la UI o del SO subyacente.

## 3. Concurrencia
Se prohíbe `time.sleep` y `cv2.imshow` en hilos de trabajo. Los fotogramas descartados se manejan vía política *latest-frame-wins*, y la UI se actualiza de forma asíncrona segura mediante Flet.
