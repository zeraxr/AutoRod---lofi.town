# 🎣 AutoRod v2.0.0 Release Notes

AutoRod v2.0 is a complete overhaul of the fishing bot for [lofi.town](https://lofi.town/). This release replaces the legacy Tkinter prototype with Clean Architecture, an adaptive computer vision pipeline, a modern Flutter-based desktop GUI (Flet), silent background clicking, and an official Windows installer.

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
| **Windows Packaging** | Monolithic exe extracted to `%TEMP%` (frequent antivirus false alarms). | Official Inno Setup installer (`AutoRod-Setup.exe`, no UAC admin prompt required) and Portable `.zip`. |
| **Antivirus & OS Trust** | UPX-compressed with no metadata, triggering heuristic detections. | Disabled UPX (`--noupx`), native Windows Application Manifest (`asInvoker`, PerMonitorV2), and official PE version info. |
| **Update Notification** | None. Manual checking required. | Prominent update button in the custom titlebar linked to GitHub Releases. |
| **Code Architecture & Tests** | Monolithic prototype scripts (`core/bot.py`, `vision/screen.py`). | Clean Architecture with decoupled domain, ports, pipeline supervisor, and 89 automated tests (84 unit + 5 architecture rules). |

---

## 📦 Distribution Packages

* **`AutoRod-v2.0.0-Setup.exe` (Recommended):** Windows installer. Installs to `%LOCALAPPDATA%\Programs\AutoRod` without needing Administrator privileges, creates desktop/start menu shortcuts, and allows clean uninstallation from Windows Settings.
* **`AutoRod-v2.0.0-Portable.zip`:** Standalone zip archive. Extract anywhere and launch `AutoRod.exe` directly.
* **`SHA256SUMS.txt`:** Cryptographic hashes to verify package integrity:
  ```powershell
  Get-FileHash .\AutoRod-v2.0.0-Setup.exe -Algorithm SHA256
  ```

---

## 🇪🇸 Resumen de Novedades en Español

AutoRod v2.0 representa una reconstrucción total del bot de pesca para [lofi.town](https://lofi.town/):

* **Modo Silencioso en Segundo Plano:** Ahora puedes pescar sin que el bot mueva el cursor de tu ratón (`PostMessage`), permitiéndote seguir trabajando o navegando mientras pesca en otra pantalla.
* **Interfaz Moderna en Flutter (Flet):** Barra de título personalizada sin marco, selector de temas, visor de rayos X en tiempo real y panel de telemetría.
* **Visión Adaptativa a 60 FPS:** Detección de diales, aguja y botones con salto automático de tarjetas de peces capturados.
* **Instalador Oficial de Windows:** Instalación limpia en espacio de usuario sin permisos UAC molestos.
* **Freno de Emergencia:** Presiona `Q` en cualquier momento para cerrar el bot inmediatamente.
