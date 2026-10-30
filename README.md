# 🎣 AutoRod - Fishing Bot for lofi.town

[![Python](https://img.shields.io/badge/Python-3.x-blue.svg)](https://www.python.org/)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.x-green.svg)](https://opencv.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

🌍 **[English](#english) | [Español](#espanol)**

---

<a id="english"></a>
## 🇬🇧 English

**AutoRod** is an automated fishing bot for **[lofi.town](https://lofi.town/)**. Built with Python and OpenCV, it uses computer vision to play the fishing minigame without memory injection or game file modifications.

### Features
* **Visual Recognition:** Uses Template Matching to time the circular skill-check minigame.
* **Auto-Fishing:** Detects "Cast" and "Reel" buttons dynamically.
* **Reward Skipping:** Analyzes white-pixel density to bypass post-catch reward cards via fast-click routines.
* **Diagnostic Mode:** Real-time preview window showing active detection boundaries.
* **Standalone Executable:** Packaged via PyInstaller into a single `.exe` file.

### How to Use
1. Download `AutoRod.exe` from the Releases tab.
2. Open **lofi.town** and stand near the water.
3. Run `AutoRod.exe`.
4. (Optional) Click **"Vista Previa" (Preview)** to verify visual detection.
5. Click **"Iniciar" (Start)** to run the bot.

### Developer Setup
```bash
git clone [https://github.com/yourusername/AutoRod.git](https://github.com/yourusername/AutoRod.git)
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

### Contributing & Feedback
Contributions and code improvements are welcome. Contact me on Discord: **`_zera.`**

### Disclaimer
For educational purposes only. Automating gameplay may violate lofi.town's Terms of Service. Use at your own risk.

---

<a id="espanol"></a>
## 🇪🇸 Español

**AutoRod** es un bot de pesca automatizado para **[lofi.town](https://lofi.town/)**. Construido con Python y OpenCV, utiliza visión por computadora para jugar el minijuego de pesca sin inyección de memoria ni modificaciones de archivos.

### Características
* **Reconocimiento Visual:** Usa *Template Matching* para sincronizar los clics en el minijuego circular.
* **Pesca Automática:** Detecta los botones "Cast" y "Reel" dinámicamente.
* **Salto de Recompensas:** Analiza la densidad de píxeles blancos para omitir las tarjetas de recompensa mediante clics rápidos.
* **Modo Diagnóstico:** Ventana de vista previa en tiempo real que muestra las áreas de detección activas.
* **Ejecutable Independiente:** Empaquetado con PyInstaller en un único archivo `.exe`.

### Cómo usar
1. Descarga `AutoRod.exe` desde la pestaña *Releases*.
2. Abre **lofi.town** y posiciónate frente al agua.
3. Ejecuta `AutoRod.exe`.
4. (Opcional) Haz clic en **"Vista Previa"** para verificar la detección visual en tu pantalla.
5. Haz clic en **"Iniciar"** para ejecutar el bot.

### Configuración para Desarrolladores
```bash
git clone [https://github.com/tuusuario/AutoRod.git](https://github.com/tuusuario/AutoRod.git)
python -m venv .venv
.venv\Scripts\activate  # En Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

### Contribuciones y Feedback
Aportes y mejoras al código son bienvenidos. Contáctame en Discord: **`_zera.`**

### Advertencia Legal
Solo para fines educativos. Automatizar el juego puede violar los Términos de Servicio de lofi.town. Úsalo bajo tu propio riesgo.
