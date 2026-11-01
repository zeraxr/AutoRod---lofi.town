"""Punto de entrada de la Interfaz de Usuario SOTA de AutoRod construida con Flet (Flutter).

Arquitectura y Componentes:
- Motor de Interfaz: Flet (Flutter Engine para Python).
- Ventana Única (Single Window Architecture): Sin ventanas emergentes (Toplevel).
- Motor de Temas Reactivo con 6 paletas WCAG 2.2 gestionado 100% en caliente.
- Barra Lateral Colapsable (Expanded 220px / Collapsed 72px) con navegación líquida.
- Botones Cinéticos con respiración de luz, foco al hover y confirmación al clic.
- Botón de Emergencia Táctico [Q] con dimensiones anti-recorte garantizadas.
- Parada de emergencia incondicional OS-level [Q] y pausa cooperativa [Shift+Q].
"""

import os
import sys
import time
import logging
import threading
import ctypes
import queue
from typing import Any
import flet as ft

from autorod.domain.ports.runner import IPipelineRunner
from autorod.domain.ports.diagnostics import IDiagnosticsRenderer
from autorod.domain.ports.vision import IVisionStrategy
from autorod.domain.ports.capture import ICaptureSource
from autorod.config import AppConfig, save_config
from autorod.infrastructure.diagnostics.queue_sink import QueueDiagnosticsSink

from autorod.infrastructure.ui.flet.theme import ThemeManager, ThemeTokens
from autorod.infrastructure.ui.flet.window_fx import FletWindowFX
from autorod.infrastructure.ui.flet.components.kinetic_button import (
    FletKineticGlowButton,
    FletKineticEmergencyButton
)
from autorod.infrastructure.ui.flet.components.gooey_sidebar import FletCollapsibleGooeySidebar
from autorod.infrastructure.ui.flet.components.viewport_view import FletDiagnosticsViewport
from autorod.infrastructure.ui.flet.components.theme_studio_view import FletThemeStudioView
from autorod.infrastructure.ui.flet.components.settings_view import FletSettingsView
from autorod.infrastructure.ui.flet.components.telemetry_view import FletTelemetryView
from autorod.infrastructure.ui.flet.components.title_bar import FletCustomTitleBar
from autorod.infrastructure.updater.github_checker import run_async_update_check
from autorod.infrastructure.ui.flet.utils import (
    safe_update,
    is_control_mounted,
    get_control_page,
    close_app_window
)

logger = logging.getLogger(__name__)


class FletTelemetryLoggingHandler(logging.Handler):
    """Redirige los registros de logging a la consola Flet de forma hilo-segura."""

    def __init__(self, app: "FletMainApp") -> None:
        super().__init__()
        self._app = app

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            if hasattr(self._app, "telemetry_view") and self._app.telemetry_view:
                self._app.telemetry_view.append_log(msg)
        except Exception:
            pass


class FletMainApp:
    """
    Coordinador maestro de la interfaz Flet para AutoRod.
    Reemplaza totalmente la arquitectura previa de Tkinter.
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
        self.runner = runner
        self.sink = diagnostics
        self.renderer = renderer
        self.vision_strategy = vision_strategy
        self.capture_source = capture_source
        self.config_data = config or AppConfig()
        self.config_path = config_path

        # 1. Gestor de Temas
        self.theme_mgr = ThemeManager.get_instance(self.config_data.ui_theme)
        self.theme_mgr.subscribe(self._on_theme_changed)

        # 2. Identidad de Proceso en Windows Shell
        FletWindowFX.setup_process_identity("autorod.automation.visual.v2", "AutoRod")

        # 3. Estados Operativos
        self._bot_running = True
        self._diagnostics_active = True
        self._current_tab = "dashboard"
        self._stop_event = threading.Event()

        # Componentes principales (se vinculan al montar la página)
        self.page: ft.Page | None = None
        self.custom_title_bar: FletCustomTitleBar | None = None
        self.sidebar: FletCollapsibleGooeySidebar | None = None
        self.viewport: FletDiagnosticsViewport | None = None
        self.settings_view: FletSettingsView | None = None
        self.theme_studio: FletThemeStudioView | None = None
        self.telemetry_view: FletTelemetryView | None = None

        # 4. Monitoreo Global de Teclas OS-Level [Q] y [Shift+Q]
        self._start_global_emergency_listener()

        # 5. Handler de Logging
        self._log_handler = FletTelemetryLoggingHandler(self)
        self._log_handler.setFormatter(logging.Formatter("%(message)s"))
        root_logger = logging.getLogger("autorod")
        root_logger.addHandler(self._log_handler)
        root_logger.setLevel(logging.INFO)

        # 6. Iniciar Pipeline Concurrente
        self.runner.start()

    def main(self, page: ft.Page) -> None:
        """Punto de montaje de la página de Flet."""
        self.page = page

        # Configurar ventana nativa
        FletWindowFX.configure_window(
            page,
            title="AutoRod",
            opacity=self.config_data.ui_transparency
        )

        if hasattr(page, "window"):
            page.window.on_event = self._on_window_event

        # Atajos locales de teclado en Flet
        page.on_keyboard_event = self._on_flet_key_event

        # 1. Sidebar Colapsable con Navegación Líquida
        self.sidebar = FletCollapsibleGooeySidebar(
            on_tab_selected=self._switch_view,
            theme_manager=self.theme_mgr
        )

        # 2. Vistas del View Deck
        self.viewport = FletDiagnosticsViewport(theme_manager=self.theme_mgr)
        self.settings_view = FletSettingsView(
            config=self.config_data,
            config_path=self.config_path,
            on_save_callback=self._on_settings_saved,
            theme_manager=self.theme_mgr
        )
        self.theme_studio = FletThemeStudioView(
            theme_manager=self.theme_mgr,
            config=self.config_data,
            config_path=self.config_path
        )
        self.telemetry_view = FletTelemetryView(theme_manager=self.theme_mgr)

        self._views: dict[str, ft.Container] = {
            "dashboard": self.viewport,
            "settings": self.settings_view,
            "palette": self.theme_studio,
            "telemetry": self.telemetry_view
        }

        # 3. Topbar de Controles
        self._breadcrumb_text = ft.Text(
            "⚡ AutoRod  /  Dashboard",
            size=13,
            weight=ft.FontWeight.BOLD,
            color="#ededed"
        )

        self._recal_btn = FletKineticGlowButton(
            text="🔄 Recalibrar",
            on_click=self.recalibrate_view,
            width=100,
            is_primary=False,
            confirmed_text="✓ CALIBRADO",
            theme_manager=self.theme_mgr
        )
        self._rayos_x_btn = FletKineticGlowButton(
            text="👁 Visor: ON",
            on_click=self.toggle_diagnostics_feed,
            width=96,
            is_primary=False,
            confirmed_text="✓ VISOR",
            theme_manager=self.theme_mgr
        )
        self._action_btn = FletKineticGlowButton(
            text="⏸ PAUSAR BOT",
            on_click=self.toggle_bot_action,
            width=132,
            is_primary=True,
            confirmed_text="✓ EJECUTADO",
            theme_manager=self.theme_mgr
        )
        self._emergency_btn = FletKineticEmergencyButton(
            on_click=self.emergency_shutdown,
            text="🚨 SALIR [Q]",
            width=128
        )

        topbar = ft.Container(
            content=ft.Row(
                controls=[
                    self._breadcrumb_text,
                    ft.Row(
                        controls=[
                            self._recal_btn,
                            self._rayos_x_btn,
                            self._action_btn,
                            self._emergency_btn
                        ],
                        spacing=8
                    )
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER
            ),
            bgcolor="#0d0e15",
            border=ft.Border.only(bottom=ft.BorderSide(1, "#181a24")),
            padding=ft.Padding.symmetric(horizontal=16, vertical=10)
        )

        self._content_area = ft.Container(
            content=self.viewport,
            expand=True
        )

        # Barra de Título Superior Personalizada (Estilo Discord / Frameless)
        self.custom_title_bar = FletCustomTitleBar(
            page=page,
            on_close=self.on_closing,
            theme_manager=self.theme_mgr
        )

        main_layout = ft.Column(
            controls=[
                self.custom_title_bar,
                ft.Row(
                    controls=[
                        self.sidebar,
                        ft.Column(
                            controls=[
                                topbar,
                                self._content_area
                            ],
                            spacing=0,
                            expand=True
                        )
                    ],
                    spacing=0,
                    expand=True
                )
            ],
            spacing=0,
            expand=True
        )

        page.add(main_layout)

        # Comprobación de actualizaciones en segundo plano
        run_async_update_check(on_update_found=self.custom_title_bar.set_update_available)

        self._start_diagnostics_stream()
        self._start_telemetry_loop()

    def _switch_view(self, tab_id: str) -> None:
        """Cambia suavemente la vista en el área central (100% en la misma ventana)."""
        self._current_tab = tab_id
        if tab_id in self._views and self._content_area:
            self._content_area.content = self._views[tab_id]
            self._update_breadcrumb_text()
            if self.page:
                self._content_area.update()
                self._breadcrumb_text.update()

    def _update_breadcrumb_text(self) -> None:
        titles = {
            "dashboard": "⚡ AutoRod  /  Dashboard",
            "settings": "⚙️ AutoRod  /  Configuración",
            "palette": "🎨 AutoRod  /  Personalizar Colores",
            "telemetry": "📊 AutoRod  /  Telemetría y Logs"
        }
        active_title = titles.get(self._current_tab, "AutoRod")
        theme_name = self.theme_mgr.current.name
        self._breadcrumb_text.value = f"{active_title}   •   Paleta: {theme_name}"

    def _on_theme_changed(self, tokens: ThemeTokens) -> None:
        self._update_breadcrumb_text()
        if self.page:
            self._breadcrumb_text.update()

    def _on_settings_saved(self, updated: AppConfig) -> None:
        self.config_data = updated
        if self.capture_source and hasattr(self.capture_source, "set_monitor"):
            self.capture_source.set_monitor(updated.monitor_index)

        if self.vision_strategy and hasattr(self.vision_strategy, "button_threshold"):
            self.vision_strategy.button_threshold = updated.button_threshold
            self.vision_strategy.cache_size_enabled = updated.cache_button_size

        if self.viewport:
            self.viewport.card_monitor.update_val(f"Monitor {updated.monitor_index}")

        # Actualización en caliente del simulador de hardware (Legacy vs Nuevo)
        if hasattr(self.runner, "supervisor") and hasattr(self.runner.supervisor, "executor"):
            try:
                from autorod.infrastructure.input.factory import InputBackendFactory
                from autorod.infrastructure.input.humanized import HumanizedInputSimulator
                from autorod.domain.models.clock import SystemClock

                raw_sim = InputBackendFactory.create(updated.input_backend)
                if updated.humanized_input:
                    new_sim = HumanizedInputSimulator(raw_sim, SystemClock())
                else:
                    new_sim = raw_sim
                self.runner.supervisor.executor.simulator = new_sim
                logger.info("[CONFIG] Simulador de hardware actualizado en caliente a: '%s'", updated.input_backend)
            except Exception as exc:
                logger.error("[CONFIG] No se pudo actualizar el simulador en caliente: %s", exc)

    def _start_diagnostics_stream(self) -> None:
        def _worker() -> None:
            while not self._stop_event.is_set():
                if not self._diagnostics_active or self._current_tab != "dashboard":
                    self._stop_event.wait(0.1)
                    continue

                latest = None
                while True:
                    try:
                        latest = self.sink.q.get_nowait()
                    except queue.Empty:
                        break

                if latest and self.viewport:
                    try:
                        img_bytes = self.renderer.render(latest)
                        self.viewport.update_image(img_bytes)
                    except Exception:
                        pass

                self._stop_event.wait(0.033)

        t = threading.Thread(target=_worker, daemon=True, name="FletDiagnosticsStream")
        t.start()

    def _start_telemetry_loop(self) -> None:
        def _worker() -> None:
            while not self._stop_event.is_set():
                try:
                    if self.viewport and is_control_mounted(self.viewport):
                        if hasattr(self.runner, "supervisor") and hasattr(self.runner.supervisor, "executor"):
                            task = getattr(self.runner.supervisor.executor, "_task", None)
                            if task and hasattr(task, "current_state"):
                                st = task.current_state.value
                                if not self._bot_running:
                                    self.viewport.card_motor.update_val("⏸ PAUSADO [Shift+Q]", color="#f59e0b", sub="Inyección detenida")
                                elif st == "SCANNING":
                                    self.viewport.card_motor.update_val("🔍 ESCANEANDO", color=self.theme_mgr.current.primary, sub="Buscando CAST! / REEL!")
                                elif st == "MINIGAME":
                                    self.viewport.card_motor.update_val("🎯 MINIJUEGO", color="#38bdf8", sub="Sincronizando aguja...")
                                elif st == "CARD_DISMISS":
                                    self.viewport.card_motor.update_val("🃏 TARJETA PEZ", color="#a855f7", sub="Saltando animación...")

                        if self.vision_strategy and hasattr(self.vision_strategy, "cached_dimensions"):
                            dims = self.vision_strategy.cached_dimensions
                            cache_on = getattr(self.vision_strategy, "cache_size_enabled", True)

                            if not cache_on:
                                self.viewport.card_cache.update_val("Modo Dinámico", color="#f59e0b", sub="Escaneo en cada frame")
                            elif dims is not None:
                                self.viewport.card_cache.update_val(
                                    f"{dims[0]}x{dims[1]} px",
                                    color=self.theme_mgr.current.primary,
                                    sub="Caché Bloqueado (Bajo CPU)"
                                )
                            else:
                                self.viewport.card_cache.update_val("Buscando...", color="#8b8d98", sub="Esperando objetivo")
                except Exception:
                    pass

                self._stop_event.wait(0.5)

        t = threading.Thread(target=_worker, daemon=True, name="FletTelemetryTick")
        t.start()

    def _start_global_emergency_listener(self) -> None:
        def _watcher() -> None:
            q_was_down = False
            while not self._stop_event.is_set():
                try:
                    q_pressed = bool(ctypes.windll.user32.GetAsyncKeyState(0x51) & 0x8000)
                    shift_pressed = bool(
                        (ctypes.windll.user32.GetAsyncKeyState(0x10) & 0x8000) or
                        (ctypes.windll.user32.GetAsyncKeyState(0xA0) & 0x8000) or
                        (ctypes.windll.user32.GetAsyncKeyState(0xA1) & 0x8000)
                    )

                    if q_pressed and not q_was_down:
                        q_was_down = True
                        if shift_pressed:
                            logger.info("[HOTKEY] Modo Pausa alternado vía hotkey global 'SHIFT + Q'.")
                            self.toggle_bot_action()
                        else:
                            # Debounce cooperativo breve para confirmar si Shift se pulsó casi al unísono
                            self._stop_event.wait(0.025)
                            shift_now = bool(
                                (ctypes.windll.user32.GetAsyncKeyState(0x10) & 0x8000) or
                                (ctypes.windll.user32.GetAsyncKeyState(0xA0) & 0x8000) or
                                (ctypes.windll.user32.GetAsyncKeyState(0xA1) & 0x8000)
                            )
                            if shift_now:
                                logger.info("[HOTKEY] Modo Pausa alternado vía hotkey global 'SHIFT + Q'.")
                                self.toggle_bot_action()
                            else:
                                logger.warning("[HOTKEY] Parada de emergencia ejecutada vía tecla global 'Q'.")
                                self.emergency_shutdown()
                                break
                    elif not q_pressed:
                        q_was_down = False
                except Exception:
                    pass
                self._stop_event.wait(0.035)

        t = threading.Thread(target=_watcher, daemon=True, name="EmergencyKeyWatcher")
        t.start()

    def _on_window_event(self, e: Any) -> None:
        etype = getattr(e, "type", "") or getattr(e, "data", "")
        if str(etype).lower() == "close":
            logger.info("Señal nativa de cierre recibida vía WindowEvent.")
            self.emergency_shutdown()

    def _on_flet_key_event(self, e: ft.KeyboardEvent) -> None:
        try:
            key = str(getattr(e, "key", "")).strip().lower()
            shift = bool(getattr(e, "shift", False))

            if key == "q":
                if shift:
                    logger.info("Modo Pausa alternado vía evento Flet 'SHIFT + Q'.")
                    self.toggle_bot_action()
                else:
                    logger.warning("Cierre de emergencia accionado vía evento Flet 'Q'.")
                    self.emergency_shutdown()
        except Exception as exc:
            logger.debug("Error procesando tecla Flet: %s", exc)

    def toggle_bot_action(self) -> None:
        self._bot_running = not self._bot_running
        if hasattr(self.runner, "supervisor") and hasattr(self.runner.supervisor, "executor"):
            self.runner.supervisor.executor.enabled = self._bot_running

        logger.info("[ESTADO] Bot %s por el usuario.", "REANUDADO" if self._bot_running else "PAUSADO")

        if self._action_btn:
            if self._bot_running:
                self._action_btn.set_text("⏸ PAUSAR BOT")
                if self.viewport:
                    self.viewport.card_motor.update_val("🎯 BOT ACTIVO", color=self.theme_mgr.current.primary, sub="Inyección activada")
            else:
                self._action_btn.set_text("⏵ INICIAR BOT")
                if self.viewport:
                    self.viewport.card_motor.update_val("⏸ PAUSADO", color="#f59e0b", sub="Solo diagnósticos visuales")

        if self.telemetry_view:
            state_msg = "Acciones del bot REANUDADAS." if self._bot_running else "Acciones del bot PAUSADAS."
            self.telemetry_view.append_log(state_msg)

    def toggle_diagnostics_feed(self) -> None:
        self._diagnostics_active = not self._diagnostics_active
        if self._rayos_x_btn:
            self._rayos_x_btn.set_text("👁 Visor: ON" if self._diagnostics_active else "👁 Visor: OFF")

    def recalibrate_view(self) -> None:
        if self.vision_strategy and hasattr(self.vision_strategy, "clear_scale_cache"):
            self.vision_strategy.clear_scale_cache()

        if self.viewport:
            self.viewport.card_cache.update_val("Recalibrando...", color="#38bdf8", sub="Re-escaneando escalas")

        if self.telemetry_view:
            self.telemetry_view.append_log("Caché temporal purgado. Recalibrando dimensiones de botones...")

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
            if self.page:
                close_app_window(self.page)
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
            if self.page:
                close_app_window(self.page)

    def run(self) -> None:
        """Inicia el ciclo principal de la aplicación Flet."""
        ft.run(self.main)

    def mainloop(self) -> None:
        """Alias para compatibilidad con ejecutores existentes."""
        self.run()
