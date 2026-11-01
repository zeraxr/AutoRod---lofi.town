# 🛡️ Guía de Seguridad, Confianza y Distribución de AutoRod

Esta guía documenta la arquitectura de seguridad de **AutoRod**, las razones técnicas detrás de las alertas heurísticas de los antivirus (falsos positivos), las herramientas implementadas para elevar la reputación del ejecutable ante el sistema operativo y el procedimiento para que los usuarios gestionen la confianza de forma cómoda y transparente.

---

## ⚖️ Declaración de Principios y Política de Funcionalidad

> [!IMPORTANT]
> **Prioridad Absoluta de la Funcionalidad:**
> En AutoRod, la fidelidad de las herramientas, la velocidad de respuesta y la precisión de la automatización visual están **por sobre cualquier intento de agradar ciegamente a los antivirus**.
>
> Si una característica esencial (como la inyección de clics via `SendInput`, la captura de pantalla en tiempo real vía `MSS/DirectX`, o la integración con drivers de bajo nivel) es clasificada por algún motor de antivirus como "sospechosa", **dicha funcionalidad se preserva intacta y se asume el riesgo técnico**, acompañándolo con transparencia de código abierto y herramientas de auditoría para el usuario.

---

## 🔍 ¿Por qué los Antivirus y Windows alertan sobre Bots de Automatización?

Cuando descargas o ejecutas un software como AutoRod, Windows Defender o herramientas de análisis como VirusTotal pueden emitir advertencias heurísticas. Esto se debe a tres factores principales:

1. **Simulación de Entrada de Hardware (`SendInput` y APIs de Ratón/Teclado):**
   * AutoRod necesita desplazar el cursor y pulsar el botón izquierdo del ratón para interactuar con el minijuego de *lofi.town*.
   * Las APIs de Windows que permiten hacer esto (`SendInput`, `SetCursorPos`, `mouse_event`) son idénticas a las que utilizan softwares legítimos de macros, herramientas de automatización de QA y asistentes de accesibilidad, pero también herramientas de control remoto no autorizadas.
   * Los motores heurísticos de antivirus suelen etiquetar esto preventivamente con categorías genéricas como `Riskware`, `Tool.AutoClicker` o `HackTool.Win32`.

2. **Captura Continua del Escritorio (Screen Ingestion):**
   * Para analizar visualmente la aguja del minijuego a 60 FPS, AutoRod lee áreas de memoria de video utilizando la librería `MSS` (llamadas nativas GDI / DirectX).
   * Algunos antivirus monitorean los procesos que acceden al búfer gráfico de la pantalla.

3. **Empaquetado de Aplicaciones Python:**
   * Al compilar scripts de Python en ejecutables `.exe` mediante empaquetadores como PyInstaller, el binario incluye un cargador base (bootloader).
   * Dado que muchos creadores novatos de malware usan empaquetadores genéricos, las firmas heurísticas de bajo costo en VirusTotal a veces marcan cualquier binario empaquetado como sospechoso por simple similitud de cabeceras.

---

## 🚀 Herramientas y Medidas Implementadas para Maximizar la Confianza

Para proteger la integridad del sistema del usuario y minimizar los falsos positivos sin tocar una sola línea de la funcionalidad del bot, AutoRod implementa los siguientes estándares industriales:

### 1. Desactivación Total de UPX (`--noupx`)
Los empaquetadores que comprimen el binario (como UPX) ofuscan las secciones del ejecutable y disparan inmediatamente alarmas en Windows Defender. En AutoRod, la compresión UPX está **completamente deshabilitada** en todos los scripts de compilación.

### 2. Metadatos de Identidad de Windows PE
El ejecutable incluye un recurso formal de versión (`VSVersionInfo`) compilado en los encabezados binarios:
* **Nombre del Producto:** AutoRod
* **Compañía / Organización:** AutoRod Open Source Project
* **Descripción:** AutoRod - Visual Automation Assistant
* **Versión Semántica:** 2.0.0.0
* **Copyright Legal:** Registrado formalmente en las propiedades del archivo.

### 3. Manifiesto de Aplicación Windows (`autorod.manifest`)
Se incrusta un manifiesto XML nativo que le informa a Windows:
* **Nivel de Privilegios:** `requestedExecutionLevel level="asInvoker"`. No solicita privilegios de Administrador de manera encubierta ni eleva privilegios sin motivo.
* **Compatibilidad de SO:** Compatibilidad declarada para Windows 10 y Windows 11.
* **DPI Awareness:** Escala correctamente sin distorsiones en monitores modernos de alta densidad de píxeles.

### 4. Instalador Asistido por Usuario (User-Space)
El instalador generado con Inno Setup instala la aplicación por defecto en:
`%LOCALAPPDATA%\Programs\AutoRod`
* **Ventaja:** No requiere permisos UAC de Administrador para su instalación estándar.
* **Desinstalación Limpia:** Permite desinstalar el programa completamente desde *Configuración > Aplicaciones instaladas* de Windows.
* **Evita `%TEMP%`:** A diferencia de ejecutables portátiles monolíticos que descomprimen DLLs en carpetas temporales (`%TEMP%`, un vector habitual de alerta para Defender), el instalador ubica los archivos en un directorio persistente y seguro.

### 5. Verificación de Integridad Criptográfica (SHA-256)
Cada versión oficial incluye un archivo `SHA256SUMS.txt`. Esto te permite verificar que el archivo que descargaste no ha sido alterado ni infectado por intermediarios.

---

## 🛠️ Guía Rápida para el Usuario

### Paso 1: Si aparece Microsoft Defender SmartScreen
SmartScreen suele mostrar una ventana azul con el texto *"Windows protegió su PC: Microsoft Defender SmartScreen impidió el inicio de una aplicación no reconocida"* simplemente porque el ejecutable es reciente y de distribución libre (sin un certificado corporativo pagado de miles de dólares):
1. Haz clic en el enlace **"Más información"** (*More info*).
2. Haz clic en el botón **"Ejecutar de todas formas"** (*Run anyway*).

---

### Paso 2: Verificar la Integridad del Archivo (SHA-256)
Abre PowerShell en la carpeta donde descargaste el instalador o el archivo comprimido y ejecuta:
```powershell
Get-FileHash .\AutoRod-Setup.exe -Algorithm SHA256
```
Compara el código devuelto con el publicado en el archivo `SHA256SUMS.txt` en la pestaña de *Releases* de GitHub. Si coinciden, el archivo es 100% auténtico e inalterado.

---

### Paso 3: Añadir Exclusión en Windows Defender (Si es necesario)
Si Windows Defender o tu antivirus bloquea el bot debido a la simulación de clics, puedes utilizar el script automatizado incluido en la carpeta `scripts/` (ejecutándolo en PowerShell como Administrador):

```powershell
# Añade la carpeta de instalación a la lista de confianza del antivirus:
powershell -ExecutionPolicy Bypass -File .\scripts\add_defender_exclusion.ps1
```

O hacerlo manualmente:
1. Abre **Seguridad de Windows** > **Protección contra virus y amenazas**.
2. En *Configuración de protección contra virus y amenazas*, selecciona **Administrar la configuración**.
3. Desplázate hasta *Exclusiones* y haz clic en **Agregar o quitar exclusiones**.
4. Haz clic en **Agregar exclusión** > **Carpeta** y selecciona `%LOCALAPPDATA%\Programs\AutoRod`.

---

### Paso 4: Firma Digital y Confianza Local (Para Desarrolladores)
Si deseas firmar tus propios ejecutables o instalar el certificado de desarrollo para que Windows nunca emita alertas en tu equipo:
```powershell
# 1. Firmar el ejecutable (genera certificado autofirmado si no tienes uno):
powershell -ExecutionPolicy Bypass -File .\scripts\sign_binary.ps1 -TargetPath "dist\AutoRod\AutoRod.exe" -CreateDevCert

# 2. Agregar el certificado generado a las autoridades de confianza del equipo:
powershell -ExecutionPolicy Bypass -File .\scripts\trust_certificate.ps1 -CerPath "dist\AutoRod\AutoRod-Dev-Certificate.cer"
```
