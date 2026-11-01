"""Punto de entrada de la Interfaz de Usuario SOTA de AutoRod.

Integra:
- Diseño Dark Mode estilizado de grado industrial (obsidian & glassmorphism).
- Motor de Temas Reactivo con 6 paletas aprobadas WCAG 2.2 gestionado 100% en el mismo programa.
- Barra lateral colapsable (Expanded 210px / Collapsed 68px) al pulsar el isotipo y nombre AutoRod.
- Navegación líquida mediante 'Gooey Bubble' con física elástica e inundación de pantalla.
- Botones cinéticos interactivos con luz interior que sigue al cursor, respiración ambiental y flood click.
- Botón de Emergencia Táctico [Q] con dibujo vectorial en Canvas y medidas garantizadas anti-recorte.
- Efectos de ventana transparente / Acrylic / Mica y correspondencia de iconos con el sistema operativo.
- Parada de emergencia incondicional global con [Q] y pausa cooperativa con [Shift+Q].
"""

import os
import sys
import time
import logging
import threading
import ctypes
from typing import Any
import tkinter as tk
from tkinter import ttk
from pathlib import Path
import mss

from autorod.domain.ports.runner import IPipelineRunner
from autorod.domain.ports.diagnostics import IDiagnosticsRenderer
from autorod.domain.ports.vision import IVisionStrategy
from autorod.domain.ports.capture import ICaptureSource
from autorod.config import AppConfig, save_config
from autorod.infrastructure.diagnostics.queue_sink import QueueDiagnosticsSink
from autorod.infrastructure.ui.tk.diagnostics_view import DiagnosticsCanvasView
from autorod.infrastructure.ui.tk.diagnostics_presenter import DiagnosticsPresenter

from autorod.infrastructure.ui.tk.theme import ThemeManager, ThemeTokens
from autorod.infrastructure.ui.tk.window_fx import WindowFXManager
from autorod.infrastructure.ui.tk.components.glow_button import (
    KineticGlowButton,
    KineticEmergencyButton,
    _draw_rounded_polygon,
    _blend_color
)
from autorod.infrastructure.ui.tk.components.gooey_nav import CollapsibleGooeySidebar
from autorod.infrastructure.ui.tk.components.theme_studio_view import ThemeStudioView
from autorod.infrastructure.ui.tk.components.metric_card import KineticMetricCard

logger = logging.getLogger(__name__)


class TkTelemetryHandler(logging.Handler):
    """Redirige los registros de logging a la consola visual de la UI de forma hilo-segura."""

    def __init__(self, app: "MainApp") -> None:
        super().__init__()
        self._app = app

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            if self._app.winfo_exists():
                self._app.after(0, lambda m=msg: self._app.append_log(m))
        except Exception:
            pass


class MainApp(tk.Tk):
    """
    Ventana principal de AutoRod.
    Diseño visual Dark Mode elegante, responsivo, con bordes redondeados modernos,
    identidad de proceso 'AutoRod' en Windows Task Manager, visualización exclusiva
    del logotipo en la barra lateral, y cerrado de emergencia global incondicional con 'Q'.
    """

    def __init__(
        self,
        runner: IPipelineRunner,
        diagnostics: QueueDiagnosticsSink,
        renderer: IDiagnosticsRenderer,
        vision_strategy: IVisionStrategy | None = None,
        capture_source: ICaptureSource | None = None,
        config: AppConfig | None = None,
        config_path: str = "config.toml"
    ) -> None:
        super().__init__()
        self.runner = runner
        self.sink = diagnostics
        self.renderer = renderer
        self.vision_strategy = vision_strategy
        self.capture_source = capture_source
        self.config_data = config or AppConfig()
        self.config_path = config_path

        # 1. Gestor de Temas Reactivo
        self.theme_mgr = ThemeManager.get_instance(self.config_data.ui_theme)
        self.theme_mgr.subscribe(self._on_theme_changed)

        # 2. Identidad del proceso en Windows Shell y Task Manager
        WindowFXManager.setup_process_identity("autorod.automation.visual.v2", "AutoRod")

        # 3. Propiedades y Estilizado de Ventana
        self.title("AutoRod")
        self.geometry("1040x710")
        self.minsize(840, 600)
        self.configure(bg="#090a0f")

        self._is_topmost = True
        self.wm_attributes("-topmost", True)
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # 4. Transparencia de Ventana y Efectos Nativos DWM
        WindowFXManager.apply_dark_mode_and_acrylic(self, use_acrylic=True)
        WindowFXManager.apply_transparency(self, self.config_data.ui_transparency)

        # 5. Iconos Oficiales
        self._loaded_icons = WindowFXManager.load_and_set_icons(self)

        # 6. Monitoreo Global de Teclas: 'SHIFT + Q' (Pausar/Reanudar) y 'Q' (Emergencia)
        self._stop_event = threading.Event()
        self._start_global_emergency_listener()

        # Atajos de Teclado locales en Tkinter
        self.bind_all("<Shift-Key-q>", lambda e: self._handle_shift_q())
        self.bind_all("<Shift-Key-Q>", lambda e: self._handle_shift_q())
        self.bind_all("<Key-q>", lambda e: self._handle_plain_q(e))
        self.bind_all("<Key-Q>", lambda e: self._handle_plain_q(e))

        # Estado del Bot y Visor
        self._bot_running = True
        self._diagnostics_active = True
        self._current_tab = "dashboard"

        # 7. Construcción de Layout Principal
        self._build_main_layout()

        # 8. Logging en vivo
        self._log_handler = TkTelemetryHandler(self)
        self._log_handler.setFormatter(logging.Formatter("%(message)s"))
        root_logger = logging.getLogger("autorod")
        root_logger.addHandler(self._log_handler)
        root_logger.setLevel(logging.INFO)

        # 9. Presentador MVP enlazado al Canvas
        self.presenter = DiagnosticsPresenter(self.view, self.sink, self.renderer)
        self.presenter.start_polling()

        # 10. Timer Periódico de Telemetría (Tarjetas Métricas)
        self._schedule_telemetry_tick()

        # 11. Iniciar Pipeline Concurrente
        self.runner.start()

    def _on_theme_changed(self, tokens: ThemeTokens) -> None:
        """Actualiza la barra de estado y los acentos visuales."""
        if hasattr(self, "_breadcrumb_lbl") and self._breadcrumb_lbl.winfo_exists():
            self._update_breadcrumb_text()

    # -------------------------------------------------------------------------
    # IDENTIDAD Y HOTKEYS DE EMERGENCIA
    # -------------------------------------------------------------------------
    def _start_global_emergency_listener(self) -> None:
        """
        Inicia un vigilante de hardware a nivel OS en un hilo de fondo.
        Diferencia entre:
          - 'SHIFT + Q': Pausa o reanuda el bot sin cerrar la ventana.
          - 'Q' (sin Shift): Cierre incondicional de emergencia.
        """
        def _watcher() -> None:
            shift_q_latched = False
            while not self._stop_event.is_set():
                try:
                    q_pressed = bool(ctypes.windll.user32.GetAsyncKeyState(0x51) & 0x8000)
                    shift_pressed = bool(
                        (ctypes.windll.user32.GetAsyncKeyState(0x10) & 0x8000) or
                        (ctypes.windll.user32.GetAsyncKeyState(0xA0) & 0x8000) or
                        (ctypes.windll.user32.GetAsyncKeyState(0xA1) & 0x8000)
                    )

                    if q_pressed and shift_pressed:
                        if not shift_q_latched:
                            shift_q_latched = True
                            logger.info("Modo Pausa alternado vía hotkey global 'SHIFT + Q'.")
                            self.after(0, self.toggle_bot_action)
                    elif q_pressed and not shift_pressed:
                        logger.warning("Parada de emergencia ejecutada vía tecla global 'Q'.")
                        self.after(0, self.emergency_shutdown)
                        break
                    else:
                        shift_q_latched = False
                except Exception:
                    pass
                self._stop_event.wait(0.035)

        t = threading.Thread(target=_watcher, daemon=True, name="EmergencyKeyWatcher")
        t.start()

    def _handle_shift_q(self) -> str:
        self.toggle_bot_action()
        return "break"

    def _handle_plain_q(self, event: Any) -> str | None:
        if not (event.state & 0x0001):
            self.emergency_shutdown()
            return "break"
        return None

    # -------------------------------------------------------------------------
    # CONSTRUCCIÓN DEL LAYOUT PRINCIPAL (TODO EN LA MISMA VENTANA)
    # -------------------------------------------------------------------------
    def _build_main_layout(self) -> None:
        self._main_container = tk.Frame(self, bg="#090a0f")
        self._main_container.pack(fill=tk.BOTH, expand=True)

        # 1. Barra Lateral Colapsable con Navegación Gooey
        logo_img = self._loaded_icons.get("logo_32") or self._loaded_icons.get("logo_48")
        self._sidebar = CollapsibleGooeySidebar(
            self._main_container,
            on_tab_selected=self._switch_view,
            logo_image=logo_img,
            theme_manager=self.theme_mgr
        )
        self._sidebar.pack(side=tk.LEFT, fill=tk.Y)

        # 2. Contenedor de Contenido Derecho
        self._right_container = tk.Frame(self._main_container, bg="#090a0f")
        self._right_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Barra Superior de Controles
        self._build_topbar(self._right_container)

        # Área de Vistas Intercambiables (100% integradas dentro del mismo programa)
        self._view_deck = tk.Frame(self._right_container, bg="#090a0f")
        self._view_deck.pack(fill=tk.BOTH, expand=True, padx=14, pady=10)

        # Crear vistas
        self._views: dict[str, tk.Frame] = {}
        self._views["dashboard"] = self._create_dashboard_view(self._view_deck)
        self._views["settings"] = self._create_settings_view(self._view_deck)
        self._views["palette"] = self._create_palette_view(self._view_deck)
        self._views["telemetry"] = self._create_telemetry_view(self._view_deck)

        self._switch_view("dashboard")

    def _build_topbar(self, parent: tk.Widget) -> None:
        """Barra superior con breadcrumb y controles de acción cinéticos perfectamente medidos."""
        topbar = tk.Frame(parent, bg="#0f1118", height=52, padx=16, pady=8)
        topbar.pack(fill=tk.X, side=tk.TOP)

        # Breadcrumb con indicador visual
        self._breadcrumb_lbl = tk.Label(
            topbar,
            text="⚡ AutoRod / Dashboard Principal",
            font=("Segoe UI", 10, "bold"),
            bg="#0f1118",
            fg="#ededed"
        )
        self._breadcrumb_lbl.pack(side=tk.LEFT)

        # Controles a la derecha sin sobrecarga visual
        right_ctrl = tk.Frame(topbar, bg="#0f1118")
        right_ctrl.pack(side=tk.RIGHT)

        # Botón Recalibrar
        self._recal_btn = KineticGlowButton(
            right_ctrl,
            text="🔄 Recalibrar",
            command=self.recalibrate_view,
            width=98,
            height=34,
            is_primary=False,
            confirmed_text="✓ CALIBRADO",
            theme_manager=self.theme_mgr
        )
        self._recal_btn.pack(side=tk.LEFT, padx=(4, 0))

        # Botón Toggle Rayos X
        self._rayos_x_btn = KineticGlowButton(
            right_ctrl,
            text="👁 Visor",
            command=self.toggle_diagnostics_feed,
            width=86,
            height=34,
            is_primary=False,
            confirmed_text="✓ VISOR",
            theme_manager=self.theme_mgr
        )
        self._rayos_x_btn.pack(side=tk.LEFT, padx=(4, 0))

        # Botón Principal Cinético: Pausar / Iniciar Bot
        self._action_btn = KineticGlowButton(
            right_ctrl,
            text="⏸ PAUSAR BOT",
            command=self.toggle_bot_action,
            width=132,
            height=34,
            is_primary=True,
            confirmed_text="✓ EJECUTADO",
            theme_manager=self.theme_mgr
        )
        self._action_btn.pack(side=tk.LEFT, padx=(6, 0))

        # Botón de Emergencia Táctico [Q] anti-recorte garantizado
        self._emergency_btn = KineticEmergencyButton(
            right_ctrl,
            command=self.emergency_shutdown,
            text="🚨 SALIR [Q]",
            width=122,
            height=34
        )
        self._emergency_btn.pack(side=tk.LEFT, padx=(8, 0))

    def _switch_view(self, tab_id: str) -> None:
        """Cambia entre las vistas del panel central dentro de la misma ventana."""
        self._current_tab = tab_id
        for tid, frame in self._views.items():
            if tid == tab_id:
                frame.pack(fill=tk.BOTH, expand=True)
            else:
                frame.pack_forget()

        self._update_breadcrumb_text()

    def _update_breadcrumb_text(self) -> None:
        titles = {
            "dashboard": "⚡ AutoRod / Dashboard Principal",
            "settings": "⚙️ AutoRod / Configuración de Parámetros",
            "palette": "🎨 AutoRod / Estudio de Personalización y Diseño",
            "telemetry": "📊 AutoRod / Telemetría y Logs en Vivo"
        }
        active_title = titles.get(self._current_tab, "AutoRod")
        theme_name = self.theme_mgr.current.name
        self._breadcrumb_lbl.config(
            text=f"{active_title}   •   Paleta: {theme_name}"
        )

    def open_theme_modal(self) -> None:
        """Acceso directo para navegar al estudio de personalización integrado."""
        self._sidebar.select_tab("palette")

    # -------------------------------------------------------------------------
    # VISTA 1: DASHBOARD / VISOR PRINCIPAL
    # -------------------------------------------------------------------------
    def _create_dashboard_view(self, parent: tk.Widget) -> tk.Frame:
        view = tk.Frame(parent, bg="#090a0f")

        # Contenedor para el Canvas de Rayos X con barra de estado superior
        canvas_card = tk.Canvas(view, bg="#090a0f", highlightthickness=0)
        canvas_card.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

        def _resize_canvas_card(event: Any) -> None:
            w, h = event.width, event.height
            canvas_card.delete("border_bg")
            _draw_rounded_polygon(
                canvas_card,
                2,
                2,
                w - 2,
                h - 2,
                radius=12,
                fill="#11131c",
                outline="#1f2334",
                width=1,
                tags="border_bg"
            )

        canvas_card.bind("<Configure>", _resize_canvas_card)

        # DiagnosticsCanvasView incrustado con márgenes suaves
        self.view = DiagnosticsCanvasView(canvas_card)
        canvas_card.create_window(6, 6, anchor="nw", window=self.view)

        def _sync_view_size(event: Any) -> None:
            vw = max(10, event.width - 12)
            vh = max(10, event.height - 12)
            self.view.config(width=vw, height=vh)

        canvas_card.bind("<Configure>", _sync_view_size, add="+")

        # Grid de Tarjetas Métricas Reactivas al Tema
        cards_frame = tk.Frame(view, bg="#090a0f")
        cards_frame.pack(fill=tk.X, side=tk.BOTTOM)

        for i in range(4):
            cards_frame.columnconfigure(i, weight=1, uniform="stat_cards")

        # Card 1: Estado del Motor
        self._card1 = KineticMetricCard(
            cards_frame,
            title="ESTADO DEL MOTOR",
            default_val="🔍 RASTREANDO...",
            subtext="Escaneo continuo",
            radius=10,
            height=76,
            theme_manager=self.theme_mgr
        )
        self._card1.grid(row=0, column=0, padx=3, sticky="nsew")

        # Card 2: Caché de Dimensiones
        self._card2 = KineticMetricCard(
            cards_frame,
            title="CACHÉ DE TAMAÑO",
            default_val="Buscando...",
            subtext="Ahorro CPU activo",
            radius=10,
            height=76,
            theme_manager=self.theme_mgr
        )
        self._card2.grid(row=0, column=1, padx=3, sticky="nsew")

        # Card 3: Monitor Activo
        mon_idx = getattr(self.capture_source, "monitor_index", self.config_data.monitor_index)
        self._card3 = KineticMetricCard(
            cards_frame,
            title="MONITOR CAPTURANDO",
            default_val=f"Monitor {mon_idx}",
            subtext="MSS Ingesta Física",
            radius=10,
            height=76,
            theme_manager=self.theme_mgr
        )
        self._card3.grid(row=0, column=2, padx=3, sticky="nsew")

        # Card 4: Rendimiento
        self._card4 = KineticMetricCard(
            cards_frame,
            title="LATENCIA ESTIMADA",
            default_val="< 20 ms",
            subtext=f"Objetivo: {self.config_data.target_fps} FPS",
            radius=10,
            height=76,
            theme_manager=self.theme_mgr
        )
        self._card4.grid(row=0, column=3, padx=3, sticky="nsew")

        return view

    # -------------------------------------------------------------------------
    # VISTA 2: CONFIGURACIÓN DE PARÁMETROS
    # -------------------------------------------------------------------------
    def _create_settings_view(self, parent: tk.Widget) -> tk.Frame:
        view = tk.Frame(parent, bg="#090a0f")

        panel = tk.Frame(view, bg="#11131c", padx=24, pady=20)
        panel.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            panel,
            text="Parámetros de Ejecución y Captura Física",
            font=("Segoe UI", 12, "bold"),
            bg="#11131c",
            fg="#ffffff"
        ).pack(anchor="w", pady=(0, 16))

        # --- Campo 1: Monitor ---
        f1 = tk.Frame(panel, bg="#11131c")
        f1.pack(fill=tk.X, pady=6)
        tk.Label(
            f1,
            text="Monitor Físico de Captura:",
            font=("Segoe UI", 9, "bold"),
            bg="#11131c",
            fg="#ededed",
            width=26,
            anchor="w"
        ).pack(side=tk.LEFT)

        available_monitors = self._get_monitors_list()
        self._monitor_var = tk.StringVar(value=f"Monitor {self.config_data.monitor_index}")
        self._monitor_cb = ttk.Combobox(
            f1,
            textvariable=self._monitor_var,
            values=[m["label"] for m in available_monitors],
            state="readonly",
            width=28
        )
        self._monitor_cb.pack(side=tk.LEFT, padx=6)

        # --- Campo 2: Caché de Dimensiones ---
        f2 = tk.Frame(panel, bg="#11131c")
        f2.pack(fill=tk.X, pady=6)
        tk.Label(
            f2,
            text="Modo Caché de Tamaño:",
            font=("Segoe UI", 9, "bold"),
            bg="#11131c",
            fg="#ededed",
            width=26,
            anchor="w"
        ).pack(side=tk.LEFT)

        self._cache_var = tk.BooleanVar(value=self.config_data.cache_button_size)
        self._cache_chk = tk.Checkbutton(
            f2,
            text="Guardar tamaño detectado (Mínimo uso de CPU/RAM - Recomendado)",
            variable=self._cache_var,
            font=("Segoe UI", 9),
            bg="#11131c",
            fg="#3ecf8e",
            activebackground="#11131c",
            activeforeground="#3ecf8e",
            selectcolor="#1c1d24",
            cursor="hand2"
        )
        self._cache_chk.pack(side=tk.LEFT, padx=6)

        # --- Campo 3: Sensibilidad ---
        f3 = tk.Frame(panel, bg="#11131c")
        f3.pack(fill=tk.X, pady=6)
        tk.Label(
            f3,
            text="Sensibilidad de Detección:",
            font=("Segoe UI", 9, "bold"),
            bg="#11131c",
            fg="#ededed",
            width=26,
            anchor="w"
        ).pack(side=tk.LEFT)

        self._thresh_var = tk.DoubleVar(value=self.config_data.button_threshold)
        self._thresh_scale = tk.Scale(
            f3,
            from_=0.45,
            to=0.85,
            resolution=0.01,
            orient=tk.HORIZONTAL,
            variable=self._thresh_var,
            bg="#161824",
            fg="#f1f5f9",
            highlightthickness=0,
            troughcolor="#202436",
            activebackground="#3ecf8e",
            length=180
        )
        self._thresh_scale.pack(side=tk.LEFT, padx=6)

        # --- Campo 4: Backend de Entrada ---
        f4 = tk.Frame(panel, bg="#11131c")
        f4.pack(fill=tk.X, pady=6)
        tk.Label(
            f4,
            text="Simulador de Hardware:",
            font=("Segoe UI", 9, "bold"),
            bg="#11131c",
            fg="#ededed",
            width=26,
            anchor="w"
        ).pack(side=tk.LEFT)

        self._backend_var = tk.StringVar(value=self.config_data.input_backend)
        backend_cb = ttk.Combobox(
            f4,
            textvariable=self._backend_var,
            values=["sendinput", "interception", "fake"],
            state="readonly",
            width=28
        )
        backend_cb.pack(side=tk.LEFT, padx=6)

        # --- Separador ---
        tk.Frame(panel, bg="#1c1f2b", height=1).pack(fill=tk.X, pady=16)

        # Botón Guardar y Aplicar Cambios
        btn_box = tk.Frame(panel, bg="#11131c")
        btn_box.pack(anchor="w")

        save_btn = KineticGlowButton(
            btn_box,
            text="💾 Guardar Parámetros",
            command=self._apply_settings,
            width=200,
            height=36,
            is_primary=True,
            confirmed_text="✓ GUARDADOS",
            theme_manager=self.theme_mgr
        )
        save_btn.pack(side=tk.LEFT)

        self._settings_toast = tk.Label(
            btn_box,
            text="",
            font=("Segoe UI", 9, "bold"),
            bg="#11131c",
            fg="#3ecf8e"
        )
        self._settings_toast.pack(side=tk.LEFT, padx=12)

        return view

    # -------------------------------------------------------------------------
    # VISTA 3: ESTUDIO DE PERSONALIZACIÓN Y PALETAS (TODO EN LA MISMA VENTANA)
    # -------------------------------------------------------------------------
    def _create_palette_view(self, parent: tk.Widget) -> tk.Frame:
        """Crea la vista de personalización de temas integrada directamente en la aplicación."""
        return ThemeStudioView(
            parent,
            theme_manager=self.theme_mgr,
            app_config=self.config_data,
            config_path=self.config_path,
            on_transparency_changed=lambda val: WindowFXManager.apply_transparency(self, val)
        )

    def _get_monitors_list(self) -> list[dict[str, Any]]:
        monitors = []
        try:
            with mss.MSS() as sct:
                for i in range(1, len(sct.monitors)):
                    m = sct.monitors[i]
                    monitors.append({
                        "index": i,
                        "label": f"Monitor {i} ({m['width']}x{m['height']})"
                    })
        except Exception:
            monitors.append({"index": 1, "label": "Monitor 1 (1920x1080)"})
        return monitors

    def _apply_settings(self) -> None:
        try:
            mon_label = self._monitor_var.get()
            import re
            m = re.search(r"Monitor\s+(\d+)", mon_label)
            new_mon_idx = int(m.group(1)) if m else 1

            new_cache_enabled = self._cache_var.get()
            new_threshold = round(self._thresh_var.get(), 2)
            new_backend = self._backend_var.get()

            if self.capture_source and hasattr(self.capture_source, "set_monitor"):
                self.capture_source.set_monitor(new_mon_idx)

            if self.vision_strategy and hasattr(self.vision_strategy, "button_threshold"):
                self.vision_strategy.button_threshold = new_threshold
                self.vision_strategy.cache_size_enabled = new_cache_enabled
                if not new_cache_enabled:
                    self.vision_strategy.clear_scale_cache()

            updated_config = AppConfig(
                target_fps=self.config_data.target_fps,
                input_backend=new_backend,
                vision_strategy=self.config_data.vision_strategy,
                capture_source=self.config_data.capture_source,
                monitor_index=new_mon_idx,
                button_threshold=new_threshold,
                cache_button_size=new_cache_enabled,
                humanized_input=self.config_data.humanized_input,
                ui_theme=self.theme_mgr.current_id,
                ui_transparency=self.config_data.ui_transparency
            )
            self.config_data = updated_config
            save_config(updated_config, self.config_path)

            self._card3.update_val(f"Monitor {new_mon_idx}")
            self._settings_toast.config(text="✓ Parámetros aplicados.", fg=self.theme_mgr.current.primary)
            self.after(3500, lambda: self._settings_toast.config(text=""))
        except Exception as exc:
            self._settings_toast.config(text=f"Error: {exc}", fg="#ef4444")

    # -------------------------------------------------------------------------
    # VISTA 4: TELEMETRÍA Y LOGS
    # -------------------------------------------------------------------------
    def _create_telemetry_view(self, parent: tk.Widget) -> tk.Frame:
        view = tk.Frame(parent, bg="#090a0f")

        panel = tk.Frame(view, bg="#11131c", padx=16, pady=14)
        panel.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            panel,
            text="Registro de Eventos y Telemetría SOTA",
            font=("Segoe UI", 11, "bold"),
            bg="#11131c",
            fg="#ededed"
        ).pack(anchor="w", pady=(0, 8))

        self._log_text = tk.Text(
            panel,
            bg="#0b0c12",
            fg="#3ecf8e",
            font=("Consolas", 9),
            relief="flat",
            bd=0,
            padx=10,
            pady=10
        )
        self._log_text.pack(fill=tk.BOTH, expand=True)
        self._log_text.insert(tk.END, "[SISTEMA] AutoRod inicializado con motor cinético.\n")
        self._log_text.insert(tk.END, "[INICIADO] Pipeline Productor-Consumidor activo a 60 FPS.\n")

        return view

    def append_log(self, text: str) -> None:
        try:
            self._log_text.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {text}\n")
            self._log_text.see(tk.END)
        except Exception:
            pass

    # -------------------------------------------------------------------------
    # TELEMETRÍA Y ACCIONES DE CICLO DE VIDA
    # -------------------------------------------------------------------------
    def _schedule_telemetry_tick(self) -> None:
        if not self.winfo_exists():
            return

        try:
            # 1. Estado del motor
            if hasattr(self.runner, "supervisor") and hasattr(self.runner.supervisor, "executor"):
                task = getattr(self.runner.supervisor.executor, "_task", None)
                if task and hasattr(task, "current_state"):
                    st = task.current_state.value
                    if not self._bot_running:
                        self._card1.update_val("⏸ PAUSADO [Shift+Q]", color="#f59e0b", sub="Inyección detenida")
                    elif st == "SCANNING":
                        self._card1.update_val("🔍 ESCANEANDO", color=self.theme_mgr.current.primary, sub="Buscando CAST! / REEL!")
                    elif st == "MINIGAME":
                        self._card1.update_val("🎯 MINIJUEGO", color="#38bdf8", sub="Sincronizando aguja...")
                    elif st == "CARD_DISMISS":
                        self._card1.update_val("🃏 TARJETA PEZ", color="#a855f7", sub="Saltando animación...")

            # 2. Caché de dimensiones
            if self.vision_strategy and hasattr(self.vision_strategy, "cached_dimensions"):
                dims = self.vision_strategy.cached_dimensions
                cache_on = getattr(self.vision_strategy, "cache_size_enabled", True)

                if not cache_on:
                    self._card2.update_val("Modo Dinámico", color="#f59e0b", sub="Escaneo en cada frame")
                elif dims is not None:
                    self._card2.update_val(
                        f"{dims[0]}x{dims[1]} px",
                        color=self.theme_mgr.current.primary,
                        sub="Caché Bloqueado (Bajo CPU)"
                    )
                else:
                    self._card2.update_val("Buscando...", color="#8b8d98", sub="Esperando objetivo")
        except Exception:
            pass

        self.after(500, self._schedule_telemetry_tick)

    def toggle_topmost(self) -> None:
        self._is_topmost = not self._is_topmost
        self.wm_attributes("-topmost", self._is_topmost)

    def toggle_bot_action(self) -> None:
        self._bot_running = not self._bot_running
        if hasattr(self.runner, "supervisor"):
            self.runner.supervisor.executor.enabled = self._bot_running

        if self._bot_running:
            self._action_btn.set_text("⏸ PAUSAR BOT")
            self._card1.update_val("🎯 BOT ACTIVO", color=self.theme_mgr.current.primary, sub="Inyección activada")
            self.append_log("Acciones del bot REANUDADAS.")
        else:
            self._action_btn.set_text("⏵ INICIAR BOT")
            self._card1.update_val("⏸ PAUSADO", color="#f59e0b", sub="Solo diagnósticos visuales")
            self.append_log("Acciones del bot PAUSADAS por el usuario.")

    def toggle_diagnostics_feed(self) -> None:
        self._diagnostics_active = not self._diagnostics_active
        if self._diagnostics_active:
            self._rayos_x_btn.set_text("👁 Visor: ON")
            self.presenter.start_polling()
        else:
            self._rayos_x_btn.set_text("👁 Visor: OFF")

    def recalibrate_view(self) -> None:
        if self.vision_strategy and hasattr(self.vision_strategy, "clear_scale_cache"):
            self.vision_strategy.clear_scale_cache()

        if hasattr(self.view, "_image_item_id"):
            self.view._image_item_id = None

        self._card2.update_val("Recalibrando...", color="#38bdf8", sub="Re-escaneando escalas")
        self.append_log("Caché temporal purgado. Re-escaneando dimensiones del botón...")

    def emergency_shutdown(self) -> None:
        logger.warning("Cerrado de emergencia accionado por el usuario [Q].")
        self._stop_event.set()
        try:
            if hasattr(self.runner, "supervisor"):
                self.runner.supervisor.executor.enabled = False
            self.runner.stop()
        except Exception:
            pass
        finally:
            try:
                self.destroy()
            except Exception:
                pass
            os._exit(0)

    def on_closing(self) -> None:
        self._stop_event.set()
        try:
            if hasattr(self.runner, "supervisor"):
                self.runner.supervisor.executor.enabled = False
            self.runner.stop()
            self.runner.join()
        except Exception:
            pass
        finally:
            self.destroy()
