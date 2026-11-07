# 🎣 AutoRod

Bot de pesca para [lofi.town](https://lofi.town/) usando visión por computadora.

[![Python](https://img.shields.io/badge/Python-3.14-blue.svg)](https://www.python.org/)
[![OpenCV](https://img.shields.io/badge/OpenCV-5.x-green.svg)](https://opencv.org/)
[![Flet](https://img.shields.io/badge/UI-Flet-02569B.svg)](https://flet.dev/)
[![Game](https://img.shields.io/badge/Game-lofi.town-ff69b4.svg)](https://lofi.town/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

🇺🇸 **[English](#english)** | 🇨🇱 **[Español](#español)**

---

<a id="english"></a>
## 🇺🇸 English

**AutoRod** is a fishing bot for **[lofi.town](https://lofi.town/)**. It uses computer vision to detect the fishing minigame, hit the target on time, cast the rod, and skip catch rewards. It works purely by looking at the screen and simulating mouse clicks, without modifying the browser or injecting into game memory.

### What it does
* **Auto-fishing:** Detects "Cast" and "Reel" buttons automatically.
* **Minigame timing:** Watches the dial and clicks when the needle is on the green target.
* **Reward skipping:** Clicks past fish reward cards quickly to keep fishing.
* **Fast native clicking:** Uses native Windows `SendInput` APIs for fast, millisecond-precise mouse clicks. *(Note: Silent background mode is experimental and in development; the bot actively moves the cursor to click).*
* **Preview window:** Shows what the bot sees and where it is clicking in real time.
* **Emergency stop & shortcuts:** Press `Shift+Q` to toggle pause, or `Alt+Q` (Left Alt + Q) for emergency shutdown. *(Note: F8/F9 keys are reserved for future releases)*.

### ⚠️ Browser Compatibility (Opera GX Warning)
> [!WARNING]
> **AutoRod does not work properly with Opera GX.**
> Opera GX aggressively throttles and limits CPU resources (via its built-in CPU/RAM limiters and background tab throttling), which starves the computer vision pipeline required for real-time target recognition and minigame detection.
> **Recommendation:** Please play the game on **Google Chrome, Brave, Mozilla Firefox, or Microsoft Edge** for smooth, accurate performance.

### Download
Grab the latest release from the **[Releases](../../releases)** tab:
* **Portable (`AutoRod-v2.2.0-Portable.zip`):** Standalone version. Unzip and run `AutoRod.exe` directly. No install needed.
*(Note: A dedicated setup installer is currently in development and will be included in future releases).*

### Note about Antivirus
Because AutoRod captures the screen and sends mouse clicks, some antivirus software might flag it as an auto-clicker or riskware. This is normal for automation tools. If Windows Defender blocks it, you can add an exclusion to the install folder using:
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\add_defender_exclusion.ps1
```
For more details, see [docs/SECURITY_AND_TRUST.md](docs/SECURITY_AND_TRUST.md).

### Run from Source
```bash
git clone https://github.com/zeraxr/AutoRod.git
cd AutoRod
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# Run
python main.py

# Tests
$env:PYTHONPATH="src"
python -m unittest discover -s tests
```

---

<a id="español"></a>
<a id="espanol"></a>
## 🇨🇱 Español

**AutoRod** es un bot de pesca para **[lofi.town](https://lofi.town/)**. Usa visión por computadora para detectar el minijuego de pesca, acertar a tiempo, lanzar la caña y saltar las recompensas. Funciona mirando la pantalla y simulando clics, sin inyectar memoria ni modificar el juego.

### Qué hace
* **Pesca automática:** Detecta los botones "Cast" y "Reel" de forma automática.
* **Acierto en el minijuego:** Sigue el dial circular y hace clic justo cuando la aguja pasa por la zona verde.
* **Salto de recompensas:** Pasa rápido las cartas de peces capturados para seguir pescando sin pausas.
* **Clics rápidos nativos:** Utiliza la API nativa de Windows `SendInput` para clics rápidos y precisos. *(Nota: El modo en segundo plano sin mover el ratón se encuentra en fase experimental; el bot mueve el cursor para hacer clic).*
* **Visor en vivo:** Muestra en tiempo real qué está detectando el bot en pantalla.
* **Freno de emergencia y atajos:** Presiona `Shift+Q` para pausar/reanudar, o `Alt+Q` (Left Alt + Q) para cierre de emergencia. *(Nota: Las teclas F8/F9 están reservadas para futuras versiones)*.

### ⚠️ Compatibilidad de Navegadores (Aviso sobre Opera GX)
> [!WARNING]
> **AutoRod no funciona adecuadamente con el navegador Opera GX.**
> Opera GX limita drásticamente los recursos de CPU del sistema (a través de sus limitadores nativos de CPU/RAM y estrangulamiento de pestañas en segundo plano), los cuales son estrictamente necesarios para ejecutar el reconocimiento visual del bot en tiempo real.
> **Recomendación:** Se aconseja jugar en **Google Chrome, Brave, Mozilla Firefox o Microsoft Edge** para garantizar una detección fluida, rápida y precisa del minijuego.

### Descarga
Descarga la versión más reciente en la pestaña de **[Releases](../../releases)**:
* **Portable (`AutoRod-v2.2.0-Portable.zip`):** Versión independiente. Descomprime y abre `AutoRod.exe` directamente sin instalación.
*(Nota: El instalador asistido .exe está actualmente en desarrollo y se incorporará en versiones futuras).*

### Nota sobre Antivirus
Como AutoRod captura la pantalla y envía clics automáticos, algunos antivirus pueden marcarlo como auto-clicker o herramienta sospechosa. Esto es común en este tipo de programas. Si Windows Defender lo bloquea, puedes agregar la carpeta a exclusiones ejecutando:
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\add_defender_exclusion.ps1
```
Para más información, revisa [docs/SECURITY_AND_TRUST.md](docs/SECURITY_AND_TRUST.md).

### Ejecutar desde Código Fuente
```bash
git clone https://github.com/zeraxr/AutoRod.git
cd AutoRod
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# Ejecutar
python main.py

# Pruebas
$env:PYTHONPATH="src"
python -m unittest discover -s tests
```

### Contacto y Dudas
Si encuentras un error o quieres sugerir mejoras, contáctame por Discord: **`_zera.`**

### Descargo de responsabilidad
Proyecto creado con fines educativos. Usar bots puede infringir las reglas de lofi.town. Úsalo bajo tu propio criterio.
