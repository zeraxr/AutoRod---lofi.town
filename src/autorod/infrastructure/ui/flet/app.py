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
from autorod.infrastructure.ui.flet.components.skeleton_view import FletDashboardSkeleton
from autorod.infrastructure.ui.flet.components.theme_studio_view import FletThemeStudioView
from autorod.infrastructure.ui.flet.components.settings_view import FletSettingsView
from autorod.infrastructure.ui.flet.components.telemetry_view import FletTelemetryView
from autorod.infrastructure.ui.flet.components.parameters_view import FletParametersView
from autorod.infrastructure.ui.flet.components.help_view import FletHelpView
from autorod.infrastructure.ui.flet.components.title_bar import FletCustomTitleBar
from autorod.infrastructure.updater.github_checker import run_async_update_check
from autorod.infrastructure.ui.flet.utils import (
    safe_update,
    safe_page_update,
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
                if self._app.page and self._app._current_tab == "telemetry":
                    safe_page_update(self._app.page)
        except Exception:
            pass


class FletMainApp:
    """
    Coordinador maestro de la interfaz Flet para AutoRod.
    Arquitectura de ventana única sin dependencias de legacy Tkinter.
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

        # 3. Estados Operativos (Inicia pausado y en espera)
        self._bot_running = False
        self._diagnostics_active = False
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
        self.parameters_view: FletParametersView | None = None
        self.help_view: FletHelpView | None = None
        self._action_btn: Any = None
        self._preview_btn: Any = None
        self._emergency_btn: Any = None

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
        FletWindowFX.enable_background_execution()

        if hasattr(page, "window"):
            page.window.on_event = self._on_window_event

        # Atajos locales de teclado en Flet
        page.on_keyboard_event = self._on_flet_key_event

        # 1. Vistas del View Deck
        self.skeleton_view = FletDashboardSkeleton(theme_manager=self.theme_mgr)
        self.viewport = FletDiagnosticsViewport(
            theme_manager=self.theme_mgr,
            on_clear_cache=self.recalibrate_view,
            on_toggle_bot=self.toggle_bot_action,
            config=self.config_data
        )
        self.settings_view = FletSettingsView(
            config=self.config_data,
            config_path=self.config_path,
            on_save_callback=self._on_settings_saved,
            theme_manager=self.theme_mgr
        )
        self.theme_studio = FletThemeStudioView(
            theme_manager=self.theme_mgr,
            config=self.config_data,
            config_path=self.config_path,
            on_preferences_changed=self._on_preferences_changed
        )
        self.telemetry_view = FletTelemetryView(theme_manager=self.theme_mgr)
        self.parameters_view = FletParametersView(
            config=self.config_data,
            config_path=self.config_path,
            on_save_callback=self._on_settings_saved,
            theme_manager=self.theme_mgr
        )
        self.help_view = FletHelpView(theme_manager=self.theme_mgr)

        # 2. Sidebar Colapsable con Navegación Líquida (6 pestañas de Figma)
        self.sidebar = FletCollapsibleGooeySidebar(
            on_tab_selected=self._switch_view,
            theme_manager=self.theme_mgr,
            settings_view=self.settings_view
        )

        self._views: dict[str, ft.Container] = {
            "dashboard": self.viewport,
            "settings": self.settings_view,
            "palette": self.theme_studio,
            "telemetry": self.telemetry_view,
            "parameters": self.parameters_view,
            "help": self.help_view
        }

        # 3. Topbar de Controles
        self._breadcrumb_text = ft.Text(
            "Inicio",
            size=13,
            weight=ft.FontWeight.W_600,
            color=self.theme_mgr.current.text_primary
        )

        self._preview_btn = FletKineticGlowButton(
            text="Visualizar",
            icon=ft.Icons.VISIBILITY_ROUNDED,
            on_click=self.toggle_diagnostics_feed,
            width=124,
            is_primary=False,
            confirmed_text="VISOR",
            theme_manager=self.theme_mgr,
            tooltip="Previsualizar área de captura en vivo"
        )
        self._action_btn = FletKineticGlowButton(
            text="INICIAR BOT",
            icon=ft.Icons.PLAY_ARROW_ROUNDED,
            on_click=self.toggle_bot_action,
            width=140,
            is_primary=True,
            confirmed_text="EJECUTADO",
            theme_manager=self.theme_mgr,
            tooltip="Alternar ejecución del bot [Shift + Q]"
        )
        self._emergency_btn = FletKineticEmergencyButton(
            on_click=self.emergency_shutdown,
            text="SALIR [Alt+Q]",
            width=122
        )

        self._topbar = ft.Container(
            content=ft.Row(
                controls=[
                    self._breadcrumb_text,
                    ft.Row(
                        controls=[
                            self._preview_btn,
                            self._action_btn,
                            self._emergency_btn
                        ],
                        spacing=8
                    )
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER
            ),
            bgcolor=self.theme_mgr.current.shell_bg,
            border=None,
            padding=ft.Padding.symmetric(horizontal=16, vertical=8)
        )

        # Conmutador animado para transiciones fluidas entre pestañas (FADE con curvas cúbicas o INSTANTÁNEO si se desactiva)
        enable_anim = self.config_data.enable_transition_animations
        self._view_switcher = ft.AnimatedSwitcher(
            content=self.viewport,
            transition=ft.AnimatedSwitcherTransition.FADE if enable_anim else ft.AnimatedSwitcherTransition.NONE,
            duration=240 if enable_anim else 0,
            reverse_duration=180 if enable_anim else 0,
            switch_in_curve=ft.AnimationCurve.EASE_OUT_CUBIC,
            switch_out_curve=ft.AnimationCurve.EASE_IN_CUBIC,
            expand=True
        )

        self._content_area = ft.Container(
            content=self._view_switcher,
            expand=True,
            bgcolor=self.theme_mgr.current.canvas_bg,
            border_radius=ft.BorderRadius.only(top_left=16, bottom_left=16)
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
                                self._topbar,
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
        """Cambia suavemente la vista con animación fluida entre pestañas."""
        self._current_tab = tab_id
        target_view = self._views.get(tab_id)
        if target_view and self._content_area and self._view_switcher:
            self._view_switcher.content = target_view
            self._update_breadcrumb_text()
            if self.page:
                self._view_switcher.update()
                self._breadcrumb_text.update()

    def _update_breadcrumb_text(self) -> None:
        titles = {
            "dashboard": "Inicio",
            "settings": "Configuración",
            "palette": "Personalización",
            "telemetry": "Telemetría",
            "parameters": "Parámetros",
            "help": "Ayuda"
        }
        self._breadcrumb_text.value = titles.get(self._current_tab, "Inicio")

    def _on_theme_changed(self, tokens: ThemeTokens) -> None:
        self._update_breadcrumb_text()
        if hasattr(self, "_content_area") and self._content_area:
            self._content_area.bgcolor = tokens.canvas_bg
        if hasattr(self, "_topbar") and self._topbar:
            self._topbar.bgcolor = tokens.shell_bg
        if hasattr(self, "_breadcrumb_text") and self._breadcrumb_text:
            self._breadcrumb_text.color = tokens.text_primary
        if hasattr(self, "custom_title_bar") and self.custom_title_bar:
            self.custom_title_bar.apply_theme(tokens)
        if hasattr(self, "sidebar") and self.sidebar:
            self.sidebar._on_theme_updated(tokens)
        if hasattr(self, "viewport") and self.viewport:
            self.viewport._on_theme_updated(tokens)
        if hasattr(self, "settings_view") and self.settings_view:
            self.settings_view.apply_theme(tokens)
        if hasattr(self, "theme_studio") and self.theme_studio:
            self.theme_studio.apply_theme(tokens)
        if hasattr(self, "telemetry_view") and self.telemetry_view:
            self.telemetry_view.apply_theme(tokens)
        if hasattr(self, "parameters_view") and self.parameters_view:
            self.parameters_view.apply_theme(tokens)
        if hasattr(self, "help_view") and self.help_view:
            self.help_view.apply_theme(tokens)
        if self.page:
            self.page.bgcolor = tokens.shell_bg
            safe_page_update(self.page)

    def _on_preferences_changed(self, updated: Any) -> None:
        """Aplica en tiempo real los cambios del checklist de rendimiento y apariencia."""
        if isinstance(updated, dict):
            show_g = updated.get("show_greetings", self.config_data.show_greetings)
            local_t = updated.get("use_local_time", self.config_data.use_local_time)
            anim_t = updated.get("enable_transition_animations", self.config_data.enable_transition_animations)
            theme_m = updated.get("theme_mode", self.config_data.theme_mode)
            accent_c = updated.get("accent_color", self.config_data.accent_color)
            self.config_data = AppConfig(
                target_fps=self.config_data.target_fps,
                monitor_index=self.config_data.monitor_index,
                capture_source=self.config_data.capture_source,
                pause_on_defocus=self.config_data.pause_on_defocus,
                minimize_to_tray=self.config_data.minimize_to_tray,
                open_at_startup=self.config_data.open_at_startup,
                shortcut_toggle=self.config_data.shortcut_toggle,
                shortcut_stop=self.config_data.shortcut_stop,
                theme_mode=theme_m,
                accent_color=accent_c,
                show_greetings=show_g,
                use_local_time=local_t,
                enable_transition_animations=anim_t,
                language=self.config_data.language,
                profile=self.config_data.profile,
                min_confidence=self.config_data.min_confidence,
                color_tolerance=self.config_data.color_tolerance,
                search_area=self.config_data.search_area,
                cast_delay_ms=self.config_data.cast_delay_ms,
                max_wait_bite_sec=self.config_data.max_wait_bite_sec,
                retry_on_lost=self.config_data.retry_on_lost,
                pause_on_consecutive_errors=self.config_data.pause_on_consecutive_errors,
                input_backend=self.config_data.input_backend,
                vision_strategy=self.config_data.vision_strategy,
                button_threshold=self.config_data.button_threshold,
                cache_button_size=self.config_data.cache_button_size,
                humanized_input=self.config_data.humanized_input,
                ui_theme=self.config_data.ui_theme,
                ui_transparency=self.config_data.ui_transparency,
            )
            save_config(self.config_data, self.config_path)
        elif isinstance(updated, AppConfig):
            self.config_data = updated

        if self.viewport and hasattr(self.viewport, "set_show_greetings"):
            self.viewport.set_show_greetings(self.config_data.show_greetings)
        if self.viewport and hasattr(self.viewport, "set_use_local_time"):
            self.viewport.set_use_local_time(self.config_data.use_local_time)
        if self.viewport and hasattr(self.viewport, "apply_button_theme"):
            self.viewport.apply_button_theme(self.theme_mgr.current.primary)

        if self._view_switcher:
            if self.config_data.enable_transition_animations:
                self._view_switcher.duration = 240
                self._view_switcher.reverse_duration = 180
                self._view_switcher.transition = ft.AnimatedSwitcherTransition.FADE
            else:
                self._view_switcher.duration = 0
                self._view_switcher.reverse_duration = 0
                self._view_switcher.transition = ft.AnimatedSwitcherTransition.NONE

        if self.page:
            safe_page_update(self.page)

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
                from autorod.infrastructure.clock.system_clock import SystemClock

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
                        if self.page:
                            safe_page_update(self.page)
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
                                    self.viewport.card_motor.update_val("PAUSADO [Shift+Q]", color="#f59e0b", sub="En espera para iniciar")
                                elif st == "SCANNING":
                                    self.viewport.card_motor.update_val("ESCANEANDO", color=self.theme_mgr.current.primary, sub="Buscando CAST! / REEL!")
                                elif st == "MINIGAME":
                                    self.viewport.card_motor.update_val("MINIJUEGO", color="#38bdf8", sub="Sincronizando aguja...")
                                elif st == "CARD_DISMISS":
                                    self.viewport.card_motor.update_val("TARJETA PEZ", color=self.theme_mgr.current.primary, sub="Saltando animación...")

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

                        if hasattr(self.viewport, "refresh_greeting"):
                            self.viewport.refresh_greeting()

                        # Forzar refresco del árbol de Flutter incluso cuando la ventana no tiene el foco
                        if self.page:
                            safe_page_update(self.page)
                except Exception:
                    pass

                self._stop_event.wait(0.25)

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
                    lalt_pressed = bool(
                        (ctypes.windll.user32.GetAsyncKeyState(0xA4) & 0x8000) or  # VK_LMENU (Left Alt)
                        (ctypes.windll.user32.GetAsyncKeyState(0x12) & 0x8000)     # VK_MENU (Alt)
                    )

                    if q_pressed and not q_was_down:
                        q_was_down = True
                        if shift_pressed:
                            logger.info("[HOTKEY] Modo Pausa alternado vía hotkey global 'SHIFT + Q'.")
                            self.toggle_bot_action()
                        elif lalt_pressed:
                            logger.warning("[HOTKEY] Parada de emergencia ejecutada vía hotkey global 'LEFT ALT + Q'.")
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
            alt = bool(getattr(e, "alt", False))

            if key == "q":
                if shift:
                    logger.info("Modo Pausa alternado vía evento Flet 'SHIFT + Q'.")
                    self.toggle_bot_action()
                elif alt:
                    logger.warning("Cierre de emergencia accionado vía evento Flet 'LEFT ALT + Q'.")
                    self.emergency_shutdown()
            elif key == "f8":
                self.toggle_bot_action()
            elif key == "f9":
                if self._bot_running:
                    self.toggle_bot_action()
            elif key in ("1", "2", "3", "4", "5", "6"):
                tab_map = {
                    "1": "dashboard",
                    "2": "settings",
                    "3": "palette",
                    "4": "telemetry",
                    "5": "parameters",
                    "6": "help"
                }
                target_tab = tab_map.get(key)
                if target_tab and hasattr(self, "sidebar") and self.sidebar:
                    self.sidebar.select_tab(target_tab)
        except Exception as exc:
            logger.debug("Error procesando tecla Flet: %s", exc)

    def toggle_bot_action(self) -> None:
        self._bot_running = not self._bot_running
        if hasattr(self.runner, "supervisor"):
            if hasattr(self.runner.supervisor, "executor"):
                self.runner.supervisor.executor.enabled = self._bot_running
            if hasattr(self.runner.supervisor, "consumer"):
                self.runner.supervisor.consumer.enabled = self._bot_running

        logger.info("[ESTADO] Bot %s por el usuario.", "REANUDADO" if self._bot_running else "PAUSADO")

        # Al reanudar o pausar el bot, purgar la memoria de escala para que
        # al arrancar comience en búsqueda constante y limpia sin residuos previos
        if self.vision_strategy and hasattr(self.vision_strategy, "clear_scale_cache"):
            self.vision_strategy.clear_scale_cache()
            if self.viewport:
                self.viewport.card_cache.update_val("Recalibrando...", color="#38bdf8", sub="Re-escaneando escalas")

        if self._action_btn:
            if self._bot_running:
                self._action_btn.set_text("PAUSAR BOT", icon=ft.Icons.PAUSE_ROUNDED)
                if self.viewport:
                    self.viewport.card_motor.update_val("BOT ACTIVO", color=self.theme_mgr.current.primary, sub="Inyección activada")
                    self.viewport.set_bot_running(True)
            else:
                self._action_btn.set_text("INICIAR BOT", icon=ft.Icons.PLAY_ARROW_ROUNDED)
                if self.viewport:
                    self.viewport.card_motor.update_val("PAUSADO [Shift+Q]", color="#f59e0b", sub="En espera para iniciar")
                    self.viewport.set_bot_running(False)

        if self.telemetry_view:
            state_msg = "Acciones del bot INICIADAS [Shift+Q]." if self._bot_running else "Acciones del bot PAUSADAS [Shift+Q]."
            self.telemetry_view.append_log(state_msg)

        if self.page:
            safe_page_update(self.page)

    def toggle_diagnostics_feed(self) -> None:
        self._diagnostics_active = not self._diagnostics_active
        if hasattr(self.runner, "supervisor") and hasattr(self.runner.supervisor, "consumer"):
            self.runner.supervisor.consumer.preview_enabled = self._diagnostics_active
        if self.viewport:
            self.viewport.set_preview_active(self._diagnostics_active)
        if self._preview_btn:
            if self._diagnostics_active:
                self._preview_btn.set_text("Ocultar Visor", icon=ft.Icons.VISIBILITY_OFF_ROUNDED)
            else:
                self._preview_btn.set_text("Visualizar", icon=ft.Icons.VISIBILITY_ROUNDED)

        if self.telemetry_view:
            msg = "Previsualización visual activada." if self._diagnostics_active else "Previsualización visual detenida (Modo Standby)."
            self.telemetry_view.append_log(msg)

        if self.page:
            safe_page_update(self.page)

    def recalibrate_view(self) -> None:
        if self.vision_strategy and hasattr(self.vision_strategy, "clear_scale_cache"):
            self.vision_strategy.clear_scale_cache()

        if self.viewport:
            self.viewport.card_cache.update_val("Recalibrando...", color="#38bdf8", sub="Re-escaneando escalas")

        if self.telemetry_view:
            self.telemetry_view.append_log("Caché temporal purgado. Recalibrando dimensiones de botones...")

        if self.page:
            safe_page_update(self.page)

    def emergency_shutdown(self) -> None:
        logger.warning("Cerrado de emergencia accionado por el usuario [LEFT ALT + Q].")
        self._stop_event.set()
        FletWindowFX.restore_process_timers()
        try:
            if hasattr(self.runner, "supervisor"):
                self.runner.supervisor.executor.enabled = False
            self.runner.stop()
        except Exception:
            pass
        finally:
            if self.page:
                close_app_window(self.page)
            from autorod.infrastructure.ui.flet.utils import terminate_child_processes
            terminate_child_processes()
            os._exit(0)

    def on_closing(self) -> None:
        self._stop_event.set()
        FletWindowFX.restore_process_timers()
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
            from autorod.infrastructure.ui.flet.utils import terminate_child_processes
            terminate_child_processes()
            os._exit(0)

    def run(self) -> None:
        """Inicia el ciclo principal de la aplicación Flet."""
        ft.run(self.main)

    def mainloop(self) -> None:
        """Alias para compatibilidad con ejecutores existentes."""
        self.run()
