# 🎨 AutoRod UI/UX & Kinetic Design System Architecture (Flet Engine)

> [!IMPORTANT]
> **AVISO CRÍTICO PARA DESARROLLADORES:**
> **Tkinter ha sido 100% PURGADO Y ELIMINADO del repositorio.**
> La interfaz de usuario de AutoRod utiliza exclusivamente **Flet** (motor vectorial Flutter).
> - **Directorio de UI Oficial:** `src/autorod/infrastructure/ui/flet/`
> - **Regla de Pureza:** Queda prohibido importar bibliotecas de UI en las capas `domain` o `application`.

---

## 1. Principios de Diseño y Objetivos de Negocio

- **Público Objetivo:** Adultos jóvenes (18-35 años), gamers de `lofi.town` y power-users habituados a interfaces modernas (Discord, Steam Deck, Linear, Raycast, Supabase).
- **Estética:** Obsidian Dark Mode (`#090a0f`), superficies de cristal líquido glassmórfico (`#161922` con borde `#262938`), halos cinéticos de respiración y micro-interacciones a 60 FPS aceleradas por GPU (Flutter Skia/Impeller).
- **Arquitectura de Ventana Única (Single Window Experience):**
  - **Cero ventanas emergentes (`Toplevel`).**
  - Todas las herramientas, configuraciones y el **Estudio de Personalización de Colores** se ejecutan dentro del mismo viewport central mediante un sistema de mazo de vistas (*View Deck*).
- **Accesibilidad WCAG 2.2:**
  - Contraste estricto Nivel AA y AAA en las 6 paletas predefinidas (mínimo 4.5:1, alcanzando hasta 19.8:1).
  - Áreas interactivas de clic mínimo de 44×44 px o anchos tácticos protegidos.
- **Botón de Emergencia Táctico con Protección Anti-Recorte:**
  - El botón `🚨 SALIR [Q]` tiene un ancho rígido y padding interno que previene el truncamiento o clipping de texto bajo cualquier resolución o escala DPI de Windows.

---

## 2. Mapa del Módulo Flet (`src/autorod/infrastructure/ui/flet/`)

```
src/autorod/infrastructure/ui/flet/
├── __init__.py                     # Exporta FletMainApp, ThemeManager, THEME_PRESETS, FletWindowFX
├── app.py                          # Composition Root de la UI, ciclo de vida y coordinador de vistas
├── theme.py                        # Gestor reactivo de temas (Pub/Sub) y validador de contraste WCAG 2.2
├── utils.py                        # Helper de actualización hilo-segura: safe_update(control)
├── window_fx.py                    # Integración Windows Shell (AppUserModelID, DWM, opacidad dinámica)
└── components/
    ├── __init__.py                 # Exporta todos los componentes visuales
    ├── kinetic_button.py           # FletKineticGlowButton y FletKineticEmergencyButton
    ├── gooey_sidebar.py            # FletCollapsibleGooeySidebar (220px expandido / 72px colapsado)
    ├── metric_card.py              # FletMetricCard (tarjeta de telemetría glassmorphic reactiva)
    ├── viewport_view.py            # FletDiagnosticsViewport (Visor Rayos X con HUD y 4 tarjetas)
    ├── theme_studio_view.py        # FletThemeStudioView (Estudio in-window con 6 paletas y preview en vivo)
    ├── settings_view.py            # FletSettingsView (Calibración de monitor, caché, umbral, backend)
    └── telemetry_view.py           # FletTelemetryView (Consola de eventos en vivo con scroll)
```

---

## 3. Especificación Técnica de los Componentes

### 3.1. Gestor de Temas Reactivo (`theme.py`)
Implementa el patrón **Observador (Pub/Sub)** con `ThemeManager`. Cualquier componente suscrito actualiza sus colores inmediatamente cuando el usuario conmuta el tema.

#### Las 6 Paletas Predefinidas:
1. **Por defecto (`default`):** Supabase Emerald (`#3ECF8E`), WCAG 2.2 AAA (Ratio: 12.4:1).
2. **Blanco (`white`):** Studio Monochrome (`#FFFFFF`), WCAG 2.2 AAA (Ratio: 19.8:1).
3. **Rojo (`red`):** Cyberpunk Ruby (`#EF4444`), WCAG 2.2 AA (Ratio: 5.1:1).
4. **Verde GitHub (`github_green`):** GitHub Primer (`#2EA043`), WCAG 2.2 AA (Ratio: 5.76:1).
5. **Morado (`purple`):** Neon Violet (`#8B5CF6`), WCAG 2.2 AA (Ratio: 7.2:1).
6. **Celeste (`cyan`):** Electric Sky (`#38BDF8`), WCAG 2.2 AAA (Ratio: 11.2:1).

---

### 3.2. Botones Cinéticos Flet (`kinetic_button.py`)

#### `FletKineticGlowButton`:
- **Respiración de Luz (Breathing Soft Glow):** Sombra difusa reactiva con bordes dinámicos.
- **Spotlight al Cursor (Hover Focus):** Aumento de brillo en el fondo y cambio de escala (`scale=1.02`).
- **Inundación y Confirmación al Clic (Flood & Confirmation Loop):**
  Al hacer clic, el botón cambia su fondo a la paleta primaria (`primary`), emite feedback háptico visual cambiando su texto a `✓ EJECUTADO` (o el texto configurado en `confirmed_text`) y regresa automáticamente a su estado de reposo tras 900 ms.
- **API para Desarrolladores:**
  ```python
  btn = FletKineticGlowButton(
      text="⏵ INICIAR BOT",
      on_click=self.toggle_bot_action,
      width=140,
      is_primary=True,
      confirmed_text="✓ EJECUTADO",
      theme_manager=self.theme_mgr
  )
  btn.set_text("⏸ PAUSAR BOT")  # Modifica el texto en caliente con safe_update
  ```

#### `FletKineticEmergencyButton` (Anti-Recorte Garantizado):
- Fondo táctico `#241114` con borde carmesí `#ef4444` y sombra de peligro.
- Ancho forzado (mínimo 130 px) con padding de seguridad de 14 px.
- El texto `🚨 SALIR [Q]` **nunca se corta**, manteniendo legibilidad absoluta.
- Atajo directo con clic o con la tecla física `[Q]`.

---

### 3.3. Barra Lateral Colapsable (`FletCollapsibleGooeySidebar`)

- **Cabecera de Identidad:**
  - Al hacer clic en el isotipo o nombre *"AutoRod"*, la barra colapsa o se expande suavemente con animación curva `FAST_OUT_SLOWIN` a 250 ms.
  - **Estado Expandido (220 px):** Muestra el isotipo oficial, nombre del software, indicador verde pulsante (`🟢`) y los nombres de las 4 pestañas.
  - **Estado Colapsado (72 px):** Se ocultan los textos tipográficos, manteniendo los iconos centrados para maximizar el área de trabajo del visor.
- **Las 4 Pestañas:**
  1. `dashboard`: Visor en vivo de Rayos X con HUD de FPS y 4 tarjetas de telemetría.
  2. `settings`: Ajustes de monitor, umbral de matching, caché y backend de clics.
  3. `palette`: Estudio de Personalización de Temas integrado (100% in-window).
  4. `telemetry`: Registro de eventos del bot con timestamp en vivo.

---

### 3.4. Estudio de Temas Integrado en Ventana Única (`FletThemeStudioView`)

- **Sin Ventanas Emergentes:** Se despliega como la pestaña `🎨 Personalizar Colores` dentro del viewport principal.
- **Selector de Paletas:** Cuadrícula con las 6 paletas de diseño, cada una con su preview de color primario y badge de contraste WCAG 2.2.
- **Sandbox en Vivo:** Contiene un botón cinético funcional para interactuar y experimentar la animación de respiración y confirmación en tiempo real antes de guardar.
- **Slider de Transparencia de Ventana:** Control deslizante de 60% a 100% que ajusta `page.window.opacity` en tiempo real y persiste la elección en `config.toml`.

---

## 4. Guía para Agentes de IA: Cómo Referenciar y Conectar la Lógica

Si eres un agente de IA que trabaja en la lógica de negocio, detección o automatización, ten en cuenta las siguientes directrices fundamentales:

### 4.1. ¿Cómo referenciar los botones en `FletMainApp`?
Los botones principales son instancias de `FletKineticGlowButton` y `FletKineticEmergencyButton` expuestas como propiedades del objeto `FletMainApp`:

| Control | Atributo en `app` | Propósito |
| :--- | :--- | :--- |
| **Botón de Acción Bot** | `app._action_btn` | Alterna entre `⏵ INICIAR BOT` y `⏸ PAUSAR BOT`. |
| **Botón de Recalibración** | `app._recal_btn` | Pesa el comando `recalibrate_view()`, borra caché de escala. |
| **Botón de Visor Rayos X** | `app._rayos_x_btn` | Alterna el renderizado de diagnósticos visuales. |
| **Botón de Parada de Emergencia** | `app._exit_btn` | Detiene inmediatamente el pipeline y cierra la aplicación. |

### 4.2. ¿Cómo actualizar textos y estados de forma segura?
En Flet 1.0, intentar llamar a `.update()` sobre un control que no está montado en la página o desde un hilo secundario sin sincronización puede lanzar `RuntimeError: Control must be added to the page first`.
Para evitar esto, utiliza siempre la utilidad hilo-segura:
```python
from autorod.infrastructure.ui.flet.utils import safe_update

# Para botones cinéticos:
app._action_btn.set_text("⏸ PAUSAR BOT")

# Para tarjetas métricas:
app.viewport.card_fps.update_val("59.8 FPS", color="#3ecf8e", sub="Detección en tiempo real")

# Para controles genéricos de Flet:
my_control.value = "Nuevo Valor"
safe_update(my_control)
```

### 4.3. ¿Cómo añadir una nueva pestaña al Dashboard?
1. En `src/autorod/infrastructure/ui/flet/components/gooey_sidebar.py`, agrega el identificador a `TAB_ITEMS`:
   ```python
   TAB_ITEMS: list[tuple[str, str, str]] = [
       ("dashboard", ft.Icons.DASHBOARD_ROUNDED, "Dashboard"),
       ("settings", ft.Icons.TUNE_ROUNDED, "Ajustes"),
       ("palette", ft.Icons.PALETTE_ROUNDED, "Personalizar"),
       ("telemetry", ft.Icons.TERMINAL_ROUNDED, "Telemetría"),
       ("mi_nueva_pestaña", ft.Icons.AUTO_GRAPH, "Analíticas"),  # Nueva pestaña
   ]
   ```
2. Crea tu vista en `src/autorod/infrastructure/ui/flet/components/mi_vista.py` heredando de `ft.Container`.
3. En `src/autorod/infrastructure/ui/flet/app.py`, instánciala y agrégala al diccionario `self._views`:
   ```python
   self._views["mi_nueva_pestaña"] = MiNuevaVista(...)
   ```

### 4.4. Reglas Inquebrantables del Pipeline
- **NUNCA utilices `time.sleep()` en el hilo de la UI:** Bloquearía el bucle de eventos de Flet y congelaría el renderizado de Flutter.
- **Arquitectura Flet Pura:** Todos los imports de interfaz deben apuntar a `autorod.infrastructure.ui.flet`.
- **Pureza de Dominio:** Ningún módulo dentro de `src/autorod/domain/` o `src/autorod/application/` puede importar `flet` ni componentes gráficos.
