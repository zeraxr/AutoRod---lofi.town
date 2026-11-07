# 📜 Notas del Parche 2.1 — AutoRod

> *"Un buen pescador nunca culpa a su caña... pero una interfaz limpia y un dial que no falla ciertamente ayudan."*

¡Bienvenidos al **Parche 2.1 de AutoRod**! 

En esta actualización nos hemos enfocado en limpiar el tablero, simplificar la navegación y elevar la precisión del motor visual. Traemos un rediseño de interfaz siguiendo lineamientos modernos de Figma, un Centro de Ayuda integrado para resolver dudas en segundos, atajos globales de teclado y un nuevo algoritmo de auto-calibración adaptativa en 5 ciclos que garantiza clics en sub-milisegundos sin importar el zoom del navegador.

A continuación, todos los detalles del parche.

---

## 🏆 Resumen del Parche

```
✨ Centro de Ayuda integrado con guía paso a paso y diagnósticos
🎨 Barra lateral Figma 1:1 con estilo píldora activa y modo Claro/Oscuro
⚡ Calibración dinámica en 5 ciclos con fijación O(1) en memoria
🛡️ Watchdog de 90s para auto-recalibración ante cambios de ventana
⌨️ Atajos de teclado globales configurables (F8 / F9 / Q)
🗑️ Pestaña 'Parámetros' deprecada y consolidada en Configuración
```

---

## ✨ Nuevas Características & Reworks de Interfaz

### 📘 Centro de Ayuda y Soporte In-App (Nuevo)
* **Buscador interactivo en tiempo real:** Encuentra soluciones rápidas filtrando por palabras clave (calibración, resolución, zoom, atajos).
* **Guía de configuración en 4 pasos:** Instrucciones claras ilustradas para alinear el juego en el navegador con la escala recomendada.
* **Copia de diagnóstico en un clic:** Genera y copia al portapapeles la información de versión y sistema operativo para facilitar reportes.
* **Acceso directo a la comunidad:** Botón oficial vinculado a nuestro servidor de Discord para soporte y sugerencias.

### 🧭 Barra Lateral de Navegación Figma 1:1 (Rework)
* **5 Pestañas Activas:** Inicio, Configuración, Personalización, Telemetría y Ayuda.
* **Estilo Píldora Activa:** La pestaña seleccionada ahora utiliza un contenedor redondeado con contraste sobrio y tipografía nítida.
* **Colapso Suave:** Transición animada entre modo compacto (72 px) y expandido (236 px) sin descuadrar controles ni botones.
* **Diseño sin Ruido:** Se eliminaron badges numéricos distractores y logotipos duplicados para mantener el foco en la telemetría.

### 🎨 Theme Studio & Paletas de Color (Mejora)
* **Base Dual:** Conmutación formal entre modo **Oscuro** (fondo `#0e1015`) y modo **Claro** (fondo `#f8fafc`).
* **6 Acentos de Élite:** Paletas ajustadas (*Cyberpunk Cyan, Crimson Pulse, GitHub Green, Royal Purple, Solar Amber, Pure White*) garantizando cumplimiento de contraste **WCAG 2.2 AA / AAA** (> 4.5:1).

### ⌨️ Atajos de Teclado Globales (Nuevo)
* Ahora puedes pausar o reanudar el ciclo de pesca con `F8` y detenerlo con `F9` (además del freno de emergencia nativo `Q` / `Shift+Q`).
* Atajos capturados a nivel de sistema operativo para responder al instante incluso si la ventana de AutoRod está minimizada.

---

## ⚡ Motor de Visión & Calibración (Buffs & Mecánicas)

### 🎯 Calibración Dinámica en 5 Ciclos
* **Antes:** El motor intentaba bloquear la escala observada en el primer match o requería reajuste manual.
* **Ahora:** Durante los primeros 5 ciclos de pesca exitosos, el motor evalúa dinámicamente las variaciones de tamaño de los botones en pantalla. Al quinto ciclo validado, **bloquea la escala en memoria $O(1)$**, reduciendo el costo de CPU y bajando la latencia de análisis a menos de 2 ms por cuadro.

### ⏱️ Watchdog de Inactividad (90 Segundos)
* **Nueva mecánica de seguridad:** Una vez bloqueada la escala, si transcurren 90 segundos continuos sin detectar ningún elemento del juego (tiempo que supera holgadamente la espera máxima de picada), el motor asume que la ventana del navegador fue movida, minimizada o modificada en zoom, y **purga el caché automáticamente** para recalibrarse desde cero en el siguiente ciclo.

### 🔍 Detección Adaptativa de Recompensas
* **Fórmula de área dinámica:** La detección de tarjetas de peces capturados ahora calcula el umbral proporcionalmente a la resolución capturada (`área > min(8000 px, 10% de pantalla)`), evitando falsos positivos con barras de tareas o títulos de ventanas.

### 🖥️ Tolerancia a Altos Factores de Zoom
* Soporte nativo y probado en pirámides multiescala para zooms de navegador de `1.25x`, `1.50x`, `1.75x` y `2.0x` en pantallas 1080p, 1440p y 4K.

---

## 🛡️ Calidad de Vida (QoL) & Resiliencia

### 🔄 Auto-recuperación de Captura de Pantalla
* Si el Administrador de Ventanas de Windows (DWM) o un cambio de resolución genera fallos transitorios en la captura, el productor no colapsa: tras 5 fallos consecutivos reinicia silenciosamente el contexto de hardware y continúa operando con normalidad.

### 💓 Latidos de Rescate en la Cola de Ejecución
* Si la animación de pesca en el navegador sufre un congelamiento temporal o el juego pierde foco durante el minijuego, el ejecutor de acciones emite latidos periódicos en cola vacía para recuperar la máquina de estados y devolver el flujo a escaneo automático sin intervención manual.

---

## 🗑️ Deprecaciones & Cambios Fuera del Meta

| Elemento / Función | Estado Anterior | Estado Parche 2.1 | Razón del Cambio |
| :--- | :--- | :--- | :--- |
| **Pestaña 'Parámetros'** | Pestaña independiente en barra lateral | **Deprecada y eliminada** | Concentrar parámetros avanzados desestabilizaba la heurística visual; las opciones esenciales se consolidaron en el menú de Configuración. |
| **Badges numéricos en tabs** | Indicadores numéricos en iconos | **Eliminados** | Generaban ruido visual innecesario en una herramienta de productividad limpia. |
| **Logotipo duplicado en sidebar** | Ícono repetido en barra lateral | **Retirado** | El branding oficial se unificó en la barra de título superior para ganar espacio vertical. |

---

## 🐛 Corrección de Errores

* Se corrigió un problema donde el caché de escala se limpiaba erróneamente durante los tiempos pasivos de espera de picada.
* Se ajustó el contraste de los textos secundarios en el tema oscuro para asegurar legibilidad bajo luz ambiental intensa.
* Se eliminaron advertencias de hilos huérfanos al cerrar la aplicación durante una calibración activa.
* Se blindaron las llamadas de teclado para prevenir bloqueos en entornos con permisos restringidos de usuario.

---

## 📦 Paquetes de Distribución

> [!NOTE]
> **Recordatorio de Formato Portable:**
> El instalador `.exe` asistido continúa en desarrollo para asegurar una experiencia de actualización transparente. El Parche 2.1 se distribuye de manera exclusiva en versión **Portable plug-and-play**.

* **`AutoRod-v2.1.0-Portable.zip`:** Descomprimir en cualquier carpeta y ejecutar `AutoRod.exe`. No requiere permisos de Administrador ni altera el registro de Windows.
* **`SHA256SUMS.txt`:** Suma criptográfica oficial para verificar que tu descarga no esté corrupta:
  ```powershell
  Get-FileHash .\AutoRod-v2.1.0-Portable.zip -Algorithm SHA256
  ```
