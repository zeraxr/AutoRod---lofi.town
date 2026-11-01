# 🎣 AutoRod - SOTA Visual Automation Bot for lofi.town

[![Python](https://img.shields.io/badge/Python-3.14-blue.svg)](https://www.python.org/)
[![OpenCV](https://img.shields.io/badge/OpenCV-5.x-green.svg)](https://opencv.org/)
[![Flet](https://img.shields.io/badge/UI-Flet%20(Flutter)-02569B.svg)](https://flet.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

🌍 **[English](#english) | [Español](#espanol)**

---

<a id="english"></a>
## 🇬🇧 English

**AutoRod** is a next-generation automated fishing bot for **[lofi.town](https://lofi.town/)**. Built with Clean Architecture, Python, OpenCV, and a responsive Flutter-powered GUI (Flet), it uses computer vision to autonomously detect minigames, buttons, and rewards without memory injection or client modifications.

### Key Features
* **Adaptive Vision Engine:** Fast HSV contour and multi-scale template matching with auto-calibration.
* **Low-Latency Input Pipeline:** Asynchronous threaded Producer-Consumer queue with ring-0 / Win32 `SendInput` backend and humanized mouse trajectory simulation.
* **Modern Responsive Interface:** Fluid Flutter UI featuring 6 WCAG 2.2 color palettes, customizable window opacity, and real-time live telemetry diagnostics.
* **Emergency Safety Hotkeys:** Instant OS-level emergency stop with `[Q]` and cooperative pause with `[Shift+Q]`.
* **Zero-Friction Windows Distribution:** Packaged with official Windows PE version metadata, application manifest (`asInvoker`, PerMonitorV2 DPI awareness), disabled UPX to minimize false positives, and Inno Setup installer.

### Distribution & Installation
Download the latest version from the **[Releases](../../releases)** page:
1. **Official Setup Installer (`AutoRod-v2.0.0-Setup.exe`):** Recommended. Installs to user space (`%LOCALAPPDATA%\Programs\AutoRod`) without requiring administrator elevation, adds Start Menu and Desktop shortcuts, and supports clean uninstallation.
2. **Portable Package (`AutoRod-v2.0.0-Portable.zip`):** Standalone archive. Extract anywhere and launch `AutoRod.exe` directly.
3. **Integrity Verification:** Check integrity against `SHA256SUMS.txt` using PowerShell:
   ```powershell
   Get-FileHash .\AutoRod-v2.0.0-Setup.exe -Algorithm SHA256
   ```

### 🛡️ Security & Antivirus Trust Policy
> [!IMPORTANT]
> **Functionality Over False Positives:**  
> AutoRod uses low-level hardware input simulation (`SendInput`) and high-speed screen capture (`MSS`). These legitimate automation techniques are sometimes flagged as `Riskware` or `GameTool` by heuristic antivirus algorithms.
>
> In AutoRod, **application functionality and tool fidelity are strictly prioritized over catering to antivirus heuristics**. Risk is acknowledged with full open-source transparency. Read the complete guide: **[docs/SECURITY_AND_TRUST.md](docs/SECURITY_AND_TRUST.md)**.
>
> If Windows Defender alerts during installation, you can add an exclusion with our included script:
> ```powershell
> powershell -ExecutionPolicy Bypass -File .\scripts\add_defender_exclusion.ps1
> ```

### Building from Source
```bash
git clone https://github.com/zeraxr/AutoRod.git
cd AutoRod
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# Run application
python main.py

# Run quality test suite
$env:PYTHONPATH="src"
python -m unittest discover -s tests

# Build distribution packages (installer, portable zip, and checksums)
python scripts/build_distribution.py
```

---

<a id="espanol"></a>
## 🇪🇸 Español

**AutoRod** es un bot de pesca automatizado de última generación para **[lofi.town](https://lofi.town/)**. Construido bajo Clean Architecture en Python con OpenCV y una interfaz moderna en Flutter (Flet), utiliza visión por computadora pura para sincronizar el minijuego de pesca sin inyección en memoria ni manipulación de archivos del navegador.

### Características Principales
* **Motor de Visión Adaptativo:** Reconocimiento geométrico y template matching multi-escala con calibración automática.
* **Pipeline de Entrada Concurrente:** Arquitectura Productor-Consumidor con hilos desacoplados y simulación de entrada de hardware Win32 (`SendInput`) con suavizado humano opcional.
* **Interfaz Líquida y Reactiva:** Motor Flet con 6 paletas de color accesibles (WCAG 2.2), ajuste de transparencia en caliente y panel de telemetría y diagnósticos "rayos X" en vivo.
* **Controles de Emergencia:** Parada inmediata OS-level mediante tecla `[Q]` y pausa cooperativa con `[Shift+Q]`.
* **Distribución de Alta Confianza:** Empaquetado profesional sin UPX (anti falsos positivos), con metadatos oficiales PE de Windows, manifiesto formal de compatibilidad Windows 10/11 y empaquetador Inno Setup.

### Formatos de Descarga
Descarga la versión más reciente desde la sección **[Releases](../../releases)**:
1. **Instalador Oficial (`AutoRod-v2.0.0-Setup.exe`):** Recomendado. Instala en el espacio de usuario (`%LOCALAPPDATA%\Programs\AutoRod`) sin requerir permisos de Administrador, crea accesos directos y permite desinstalación limpia desde Windows.
2. **Paquete Portable (`AutoRod-v2.0.0-Portable.zip`):** Descomprime y ejecuta `AutoRod.exe` directamente sin instalación previa.
3. **Verificación de Autenticidad (SHA-256):** Comprueba que tu descarga es idéntica a la oficial con:
   ```powershell
   Get-FileHash .\AutoRod-v2.0.0-Setup.exe -Algorithm SHA256
   ```

### 🛡️ Política de Seguridad y Confianza con Antivirus
> [!IMPORTANT]
> **La Funcionalidad está por sobre la Heurística Antivirus:**  
> Debido a que AutoRod emite clics físicos de baja latencia (`SendInput`) y realiza lecturas de pantalla a alta velocidad, algunos antivirus heurísticos pueden clasificarlo preventivamente como `Riskware` o `AutoClicker`.
>
> La política de AutoRod es **priorizar la funcionalidad y potencia de las herramientas sin comprometerlas por apaciguar a los antivirus**. Dicho riesgo se asume con total transparencia de código abierto. Consulta los detalles en: **[docs/SECURITY_AND_TRUST.md](docs/SECURITY_AND_TRUST.md)**.
>
> Para registrar la exclusión en Windows Defender con un clic:
> ```powershell
> powershell -ExecutionPolicy Bypass -File .\scripts\add_defender_exclusion.ps1
> ```

### Configuración para Desarrolladores y Compilación
```bash
git clone https://github.com/zeraxr/AutoRod.git
cd AutoRod
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# Ejecutar la aplicación
python main.py

# Ejecutar la suite de pruebas unitarias
$env:PYTHONPATH="src"
python -m unittest discover -s tests

# Generar paquetes de distribución (instalador, portable y hashes)
python scripts/build_distribution.py
```

### Contribuciones y Contacto
Contribuciones, mejoras y reportes son bienvenidos. Discord: **`_zera.`**

### Advertencia Legal
Software desarrollado para fines de investigación y educativos. El uso de automatizaciones puede violar los Términos de Servicio de lofi.town. Úsalo bajo tu propia responsabilidad.
