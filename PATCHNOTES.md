# 📜 Notas del Parche 2.2 — AutoRod

> *"La precisión no es cuestión de suerte: un dial que no parpadea ante las sacudidas y una aguja perfectamente centrada marcan la diferencia entre un pez legendario y una bota rota."*

¡Bienvenidos al **Parche 2.2 de AutoRod**!

Esta versión llega cargada de optimizaciones directas al corazón del motor de visión y a la experiencia del usuario. Hemos perfeccionado el seguimiento del minijuego con memoria temporal contra sacudidas de hasta 35 fotogramas, introducido un nuevo sistema interactivo de comprobación de actualizaciones dentro de la propia aplicación que distingue entre entornos portables e instalados, solucionado el sangrado de color en los controles de interfaz y extendido el margen de rescate del minijuego a 16 segundos.

A continuación, el desglose completo de los cambios del parche.

---

## 🏆 Resumen del Parche

```
🚀 Diálogo interactivo in-app de actualizaciones con detección de entorno
🎯 Memoria temporal de 35 cuadros en el minijuego contra sacudidas y destellos
📐 Calibración de anticipación en píxeles y centrado de aguja en el dial
⏱️ Buff de rescate del minijuego: tiempo de gracia extendido de 8s a 16s
🎨 Aislamiento estricto de acento en Theme Studio (sin sangrado verde)
🔍 Diagnóstico en arranque con coordenadas de la zona de escaneo (ROI)
🏗️ Compilación nativa en C con Nuitka (PyInstaller deprecado)
📦 Distribución exclusiva en formato Portable plug-and-play
```

---

## 🚀 Sistema de Actualizaciones In-App (Nuevo)

### 🔔 Notificador y Diálogo Inteligente
* **Detección Determinista de Entorno:** El sistema ahora reconoce automáticamente si la aplicación se ejecuta como versión **Portable** (carpeta de usuario/descargas) o **Instalada** mediante instalador de sistema.
* **Flujo Asistido según Entorno:**
  * En versión **Portable**, el asistente informa sobre la nueva versión y proporciona un botón de acceso directo al repositorio oficial de GitHub para una descarga transparente.
  * En versión **Instalada**, ofrece la descarga asíncrona del instalador con barra de progreso en vivo e instalación en un clic.
* **Indicador Nítido en Barra de Título:** Un punto de estado en color celeste se activa de forma discreta únicamente cuando existe una versión superior comprobada mediante la API de GitHub.

---

## 🎯 Motor Visual & Minijuego (Buffs & Rework)

### 🛡️ Memoria de Persistencia Temporal (Anti-Jitter de 35 Frames)
* **Antes:** Si la animación del juego parpadeaba, sufría un destello de luz o una sacudida brusca de cámara, el motor perdía el dial instantáneamente y abortaba el ciclo.
* **Ahora:** Se incorporó un acumulador de tolerancia (`_dial_lost_frames`). El motor mantiene el anclaje y predicción del dial hasta durante **35 fotogramas consecutivos de sacudida** (~300-500 ms), absorbiendo caídas de cuadros del navegador y transiciones gráficas sin perder el objetivo.

### 📍 Centrado Dinámico de Aguja y Compensación de Anticipación
* **Alineación Geométrica Fina:** El cálculo del centro de clic ahora localiza el punto exacto de la aguja (`needle_cx`), reduciendo el desvío lateral a 0 px.
* **Parámetro de Anticipación (`minigame_anticipation_px`):** Permite configurar anticipación en píxeles para adaptarse a monitores con tasas de refresco dispares o retrasos de renderizado en el navegador.
* **Umbral de Dial Calibrado (0.89):** El umbral de coincidencia se ajustó a 0.89 para garantizar un 100% de inmunidad ante césped o fondos oscuros, permitiendo una detección instantánea del sector verde con solo 35% de densidad bajo la aguja.

---

## ⏱️ Resiliencia del Bucle de Pesca (Buffs a Tiempos de Espera)

### 📈 Extensión de Tiempo de Minijuego (8s ➔ 16s)
* En peces de alta rareza o animaciones con múltiples giros en el navegador, el temporizador anterior de 8 segundos podía forzar un reinicio prematuro a modo escaneo.
* El tiempo máximo antes de declarar timeout se amplió a **16.0 segundos**, garantizando que el ciclo continúe activo hasta que la captura concluya de forma natural.

---

## 🎨 Theme Studio & Interfaz de Usuario (Mejoras Visuales)

### 🧪 Erradicación de Sangrado de Color en Controles
* **Antes:** Al seleccionar paletas de acento alternativas (como Cyberpunk Cyan o Crimson Pulse), algunos interruptores de alternancia y deslizadores mostraban bordes o halos con el color verde por defecto.
* **Ahora:** Todos los controles de interfaz, switches y botones cinéticos heredan estrictamente el color de acento activo (`active_color`, `thumb_color`, `track_color`), manteniendo una armonía cromática inmaculada.

---

## 🔍 Trazabilidad y Diagnóstico de Arranque

### 📋 Registro Explícito de ROI
* Al iniciar la aplicación, la consola de diagnóstico registra detalladamente si la zona de escaneo recortada está activa, junto con sus coordenadas exactas (`(x1, y1)` a `(x2, y2)` y resolución en píxeles) y los parámetros calibrados del motor (`button_threshold`, `dial_threshold`, `anticipation_px`, ciclos requeridos y watchdog de inactividad).

---

## 🏗️ Reingeniería de Compilación: Nuitka SOTA (PyInstaller Deprecado)

### 🚀 De Bytecode Empaquetado a Código Máquina Real en C
* **El Problema con PyInstaller:** PyInstaller fue retirado de la arquitectura de AutoRod debido a su arquitectura basada en *bootloaders* genéricos precompilados, los cuales son frecuentemente señalados por motores heurísticos automatizados en VirusTotal (generando falsos positivos por comportamiento).
* **El Nuevo Motor de Compilación (Nuitka):**
  * AutoRod ahora se traduce a código fuente en **C** y se compila a código máquina nativo mediante compiladores C/C++ industriales (MSVC en Windows).
  * **Mayor Rendimiento:** Las llamadas al subsistema de visión por computadora y a las APIs de Windows operan a velocidad de C nativo, reduciendo la latencia de análisis en pantalla.
  * **Máxima Reputación y Seguridad:** Al carecer de *stubs* o descompresores temporales en memoria, el ejecutable se comporta y analiza como un binario genuino de Windows, ganando la confianza de herramientas de análisis de seguridad.

---

## 🗑️ Cambios Menores & Ajustes del Meta

| Componente | Estado Parche 2.1 | Estado Parche 2.2 | Razón del Cambio |
| :--- | :--- | :--- | :--- |
| **Motor de compilación** | PyInstaller (empaquetador) | **Nuitka (C nativo)** | Erradicar falsos positivos de VirusTotal y elevar la eficiencia. |
| **Tiempo límite de minijuego** | 8.0 segundos | **16.0 segundos** | Evitar timeouts en peces con animaciones largas. |
| **Pérdida de cuadros de dial** | 0 cuadros (pérdida inmediata) | **35 cuadros de tolerancia** | Resistencia a destellos y sacudidas gráficas. |
| **Umbral de impacto en verde** | 40% de área | **35% de área** | Respuesta más ágil al ingresar al sector óptimo. |
| **Configuración de dial** | Umbral fijo en código | **Configurable (`dial_threshold = 0.89`)** | Flexibilidad y ajuste fino desde `config.toml`. |

---

## 📦 Paquetes de Distribución

> [!NOTE]
> **Cláusula sobre el Formato de Distribución:**
> El instalador asistido tipo Setup `.exe` continúa en etapa de desarrollo y pruebas internas para garantizar una experiencia de instalación y actualización segura y sin fricciones. Por ello, el Parche 2.2 se publica exclusivamente en formato **Portable plug-and-play** (`AutoRod-v2.2.0-Portable.zip`).
> 
> * **`AutoRod-v2.2.0-Portable.zip`:** Descomprimir en cualquier carpeta y ejecutar `AutoRod.exe`. No requiere permisos de Administrador ni altera el registro de Windows.
> * **`SHA256SUMS.txt`:** Suma criptográfica oficial para validar la integridad del paquete:
>   ```powershell
>   Get-FileHash .\AutoRod-v2.2.0-Portable.zip -Algorithm SHA256
>   ```
