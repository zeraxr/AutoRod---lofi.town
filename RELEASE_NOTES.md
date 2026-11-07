# 🎣 AutoRod v2.2.0

Actualización centrada en precisión del minijuego con memoria anti-sacudidas, nuevo sistema in-app de actualizaciones y correcciones cromáticas en la interfaz.

---

### ✨ Novedades Destacadas

* **🚀 Diálogo In-App de Actualizaciones:** Comprobación interactiva desde la barra superior, con detección automática de versión Portable e información directa de nuevas versiones.
* **🎯 Tolerancia Anti-Sacudidas (35 Frames):** El motor visual mantiene el anclaje del dial del minijuego durante sacudidas de cámara, destellos o micro-tirones del navegador.
* **📍 Centrado Preciso de Aguja:** Localización sub-píxel de la punta de la aguja con soporte para compensación de anticipación (`minigame_anticipation_px`).
* **⏱️ Margen de Minijuego Extendido (16s):** Tiempo de gracia ampliado para garantizar la captura sin cortes prematuros en peces legendarios.
* **🎨 Tema Visual Puro:** Los switches y controles interactivos respetan al 100% el acento seleccionado en Theme Studio, eliminando sangrados verdosos residuales.
* **🔍 Trazabilidad de ROI en Consola:** Registro explícito en el arranque con las coordenadas exactas de la zona de escaneo y umbrales del motor.

---

### 📜 Notas Completas del Parche
Para ver el desglose técnico detallado, comparativas y notas de desarrollo estilo League of Legends, consulta:
👉 **[PATCHNOTES.md (Notas Completas del Parche 2.2)](PATCHNOTES.md)**

---

### 📦 Descarga Oficial

* **`AutoRod-v2.2.0-Portable.zip`:** Versión autónoma recomendada. Descomprimir y ejecutar `AutoRod.exe` directamente.
* **`SHA256SUMS.txt`:** Suma criptográfica de integridad:
  ```powershell
  Get-FileHash .\AutoRod-v2.2.0-Portable.zip -Algorithm SHA256
  ```

> [!NOTE]
> **Cláusula sobre el Instalador:**
> Se publica de manera exclusiva la versión **Portable** del software. El instalador con setup asistido `.exe` aún no ha sido del todo desarrollado y continúa en fase de pruebas internas para garantizar una experiencia óptima y segura; su lanzamiento oficial se incorporará en futuras versiones.
