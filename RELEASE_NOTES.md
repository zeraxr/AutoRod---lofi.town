# 🎣 AutoRod v2.0.0 Release Notes

AutoRod v2.0 is a complete overhaul of the fishing bot for [lofi.town](https://lofi.town/). This release replaces the legacy Tkinter prototype with Clean Architecture, an adaptive computer vision pipeline, a modern Flutter-based desktop GUI (Flet), silent background clicking, and standalone portable distribution.

---

## 🚀 Comparison: AutoRod v1.0 vs AutoRod v2.0

| Feature / Aspect | 🔴 AutoRod v1.0 (Legacy) | 🟢 AutoRod v2.0 (New) |
| :--- | :--- | :--- |
| **User Interface (GUI)** | Basic Tkinter window with raw buttons and standard OS frame. | Modern Flutter-based GUI (Flet) with a custom frameless titlebar, live diagnostic viewport, and 6 color themes. |
| **Click Modes (Mouse Control)** | Only physical mouse grabbing via PyAutoGUI. Interrupted PC usage. | **Silent Background Mode (PostMessage)** sends clicks directly without moving the mouse; plus low-latency **SendInput**. |
| **Vision & Minigame Detection** | Basic template matching sensitive to scaling and screen resolution. | Adaptive geometric tracking with multi-scale template pyramids, needle hit confirmation, and high-speed dial ROI tracking. |
| **Screen Capture & Performance** | Slower PyAutoGUI/PIL screenshots (~10-15 FPS) with noticeable CPU load. | High-speed DirectX/GDI capture via `MSS` running at 60 FPS with low CPU consumption. |
| **Reward Handling** | Required manual clicks or waited passively to dismiss caught fish cards. | Automatic fish catch card detection and instant click-skipping routine. |
| **Emergency Controls** | No global hotkey; required finding and clicking the stop button. | OS-level emergency stop with `[Q]` and cooperative pause with `[Shift+Q]`. |
| **Windows Packaging** | Monolithic exe extracted to `%TEMP%` (frequent antivirus false alarms). | Verified Standalone Portable package (`AutoRod-v2.0.0-Portable.zip`, zero installation required). |
| **Antivirus & OS Trust** | UPX-compressed with no metadata, triggering heuristic detections. | Disabled UPX (`--noupx`), native Windows Application Manifest (`asInvoker`, PerMonitorV2), and official PE version info. |
| **Update Notification** | None. Manual checking required. | Prominent update button in the custom titlebar linked to GitHub Releases. |
| **Code Architecture & Tests** | Monolithic prototype scripts (`core/bot.py`, `vision/screen.py`). | Clean Architecture with decoupled domain, ports, pipeline supervisor, and 89 automated tests (84 unit + 5 architecture rules). |

---

## 📦 Distribution Packages & Release Notice

> [!NOTE]
> **Notice on Windows Installer (.exe setup):**
> The dedicated Inno Setup Windows installer (`AutoRod-Setup.exe`) is currently in active refinement and has not been fully finalized. To guarantee maximum stability, safety, and a seamless plug-and-play experience, the installer has been deferred to future releases.
> AutoRod v2.0.0 is distributed exclusively as a self-contained, standalone **Portable** package.

* **`AutoRod-v2.0.0-Portable.zip` (Official Release):** Standalone archive containing the complete application bundle. No installation or Administrator privileges required. Extract anywhere and run `AutoRod.exe`.
* **`SHA256SUMS.txt`:** Cryptographic hashes to verify package integrity:
  ```powershell
  Get-FileHash .\AutoRod-v2.0.0-Portable.zip -Algorithm SHA256
  ```

---

## 🇪🇸 Resumen de Novedades y Cláusula de Distribución

> [!NOTE]
> **Cláusula sobre el Asistente de Instalación:**
> El asistente de instalación asistida para Windows (`AutoRod-Setup.exe`) no ha sido incluido en este lanzamiento dado que se encuentra en fase de desarrollo y optimización de integración. Dicha funcionalidad queda reservada para futuras versiones.
> Por este motivo, la versión v2.0.0 se entrega de forma exclusiva en formato **Portable**, garantizando ejecución inmediata sin instalaciones en el sistema ni elevación de privilegios UAC.

Novedades destacadas de AutoRod v2.0:

* **Modo Silencioso en Segundo Plano:** Pesca sin mover el cursor de tu ratón (`PostMessage`), permitiéndote trabajar o navegar mientras el bot opera en otra ventana.
* **Interfaz Moderna en Flutter (Flet):** Barra de título personalizada sin marco, selector de temas, visor de rayos X en tiempo real y panel de telemetría.
* **Visión Adaptativa a 60 FPS:** Detección de diales, aguja y botones con salto automático de tarjetas de peces capturados.
* **Freno de Emergencia:** Presiona `Q` en cualquier momento para cerrar el bot inmediatamente.
* **Distribución Portable Plug-and-Play:** Descomprime y ejecuta `AutoRod.exe` directamente.
