# 🎣 AutoRod v2.1.0

Actualización centrada en refinamiento visual (Figma 1:1), centro de ayuda in-app y estabilidad adaptativa del motor de visión.

---

### ✨ Novedades Destacadas

* **📘 Centro de Ayuda Integrado:** Buscador en tiempo real con soluciones rápidas, guía de 4 pasos para configurar tu juego y copia de diagnóstico en un clic.
* **🧭 Barra Lateral Figma 1:1:** Rediseño minimalista con pestañas sobrias en estilo píldora activa, transiciones fluidas de colapso y acceso directo a Discord.
* **🎯 Calibración Adaptativa en 5 Ciclos:** El motor evalúa 5 ciclos de pesca continuos antes de fijar la escala en memoria $O(1)$, reduciendo la latencia a <2 ms.
* **⏱️ Watchdog de Inactividad (90s):** Auto-recalibración inteligente si mueves, redimensionas o cambias el zoom del navegador.
* **🎨 Theme Studio Refinado:** Conmutación formal Claro/Oscuro y 6 paletas de acento optimizadas con estándar WCAG 2.2 AA (>4.5:1).
* **⌨️ Atajos Globales de Teclado:** Control rápido con `F8` (Pausar/Reanudar) y `F9` (Detener), además del freno de emergencia `Q`.
* **🛡️ Resiliencia de Captura:** Recuperación automática ante bloqueos temporales del Administrador de Ventanas (DWM) sin interrupciones.
* **🗑️ Simplificación de Interfaz:** Pestaña "Parámetros" deprecada y consolidada en Configuración para blindar las constantes del motor.

---

### 📜 Notas Completas del Parche
Para ver el desglose técnico detallado, comparativas y notas de desarrollo estilo League of Legends, consulta:
👉 **[PATCHNOTES.md (Notas Completas del Parche 2.1)](PATCHNOTES.md)**

---

### 📦 Descarga Oficial

* **`AutoRod-v2.1.0-Portable.zip`:** Versión autónoma recomendada. Descomprimir y ejecutar `AutoRod.exe` directamente.
* **`SHA256SUMS.txt`:** Suma criptográfica de integridad:
  ```powershell
  Get-FileHash .\AutoRod-v2.1.0-Portable.zip -Algorithm SHA256
  ```

> *Nota: El asistente de instalación asistida `.exe` continúa en desarrollo y se incluirá en futuras entregas.*
