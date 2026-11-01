"""Vista de Configuración de Parámetros en Flet para Barra Lateral (Sidebar)."""

from typing import Callable, Any
import re
import flet as ft
from autorod.infrastructure.ui.flet.theme import ThemeManager, ThemeTokens
from autorod.config import AppConfig, save_config
from autorod.infrastructure.ui.flet.components.kinetic_button import FletKineticGlowButton
from autorod.infrastructure.ui.flet.utils import safe_update
import mss


class FletSettingsView(ft.Container):
    """
    Panel de configuración de parámetros de captura, visión e inyección de hardware.
    Optimizado para integración fluida dentro de la barra lateral (Sidebar) con estructura
    limpia, sin repetición innecesaria y con hints concisos de alta legibilidad.
    """

    def __init__(
        self,
        config: AppConfig,
        config_path: str = "config.toml",
        on_save_callback: Callable[[AppConfig], None] | None = None,
        theme_manager: ThemeManager | None = None
    ) -> None:
        self._config = config
        self._config_path = config_path
        self._on_save_cb = on_save_callback
        self._theme_mgr = theme_manager or ThemeManager.get_instance()
        self._tokens = self._theme_mgr.current

        # Colecciones para reactividad de tema
        self._icon_anchors: list[ft.Container] = []
        self._hint_boxes: list[ft.Container] = []

        # ---------------------------------------------------------------------
        # 0. HEADER COMPACTO DE PARÁMETROS
        # ---------------------------------------------------------------------
        header = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.TUNE_ROUNDED, size=15, color=self._tokens.primary),
                            ft.Text(
                                "Parámetros del Sistema",
                                style=ft.TextStyle(
                                    size=12,
                                    weight=ft.FontWeight.BOLD,
                                    color="#ffffff",
                                    letter_spacing=0.2
                                )
                            )
                        ],
                        spacing=6,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER
                    ),
                    ft.Container(
                        content=ft.Text(
                            "CONFIG.TOML",
                            style=ft.TextStyle(
                                size=9,
                                weight=ft.FontWeight.W_700,
                                color="#71717a",
                                letter_spacing=0.5
                            )
                        ),
                        bgcolor="#141418",
                        border=ft.Border.all(1, "#222228"),
                        border_radius=4,
                        padding=ft.Padding.symmetric(horizontal=6, vertical=2)
                    )
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER
            ),
            padding=ft.Padding.symmetric(horizontal=4, vertical=4),
            margin=ft.Margin.only(bottom=2)
        )

        # ---------------------------------------------------------------------
        # 1. MODO DE CLICS Y SIMULACIÓN
        # ---------------------------------------------------------------------
        backend_tooltip = (
            "Modo de Clics (Simulador):\n"
            "• Modo Nuevo (PostMessage): Inyecta clics silenciosos en segundo plano sin mover el ratón físico de Windows. "
            "Ideal para trabajar, programar o navegar en tu monitor principal mientras pesca en el secundario.\n"
            "• Modo Legacy (SendInput): Mueve físicamente el cursor de Windows en la pantalla para hacer clic."
        )

        self._backend_dropdown = ft.Dropdown(
            options=[
                ft.DropdownOption("postmessage", "PostMessage (Silencioso en segundo plano)"),
                ft.DropdownOption("sendinput", "SendInput (Físico con cursor de Windows)"),
                ft.DropdownOption("interception", "Interception (Conductor Kernel Ring 0)"),
                ft.DropdownOption("fake", "Modo Pruebas (Simulado sin clics)")
            ],
            value=self._config.input_backend,
            bgcolor="#131418",
            border_color="#222329",
            focused_border_color=self._tokens.primary,
            text_size=11.5,
            content_padding=ft.Padding.symmetric(horizontal=10, vertical=6),
            tooltip=backend_tooltip,
            on_select=self._on_backend_change
        )

        self._backend_active_note = ft.Text(
            "",
            style=ft.TextStyle(size=10, color=self._tokens.primary, weight=ft.FontWeight.W_600)
        )
        self._update_backend_note(self._config.input_backend)

        block_backend = self._create_setting_block(
            icon=ft.Icons.MOUSE_ROUNDED,
            title="Modo de Inyección",
            control=self._backend_dropdown,
            hint_text="PostMessage opera en segundo plano sin mover el ratón físico de Windows. SendInput mueve el cursor real de Windows."
        )

        # ---------------------------------------------------------------------
        # 2. MONITOR FÍSICO DE CAPTURA
        # ---------------------------------------------------------------------
        monitor_tooltip = (
            "Monitor Físico de Captura:\n"
            "Selecciona la pantalla donde está abierto el juego. "
            "El bot capturará y analizará los minijuegos únicamente en este monitor."
        )

        monitors = self._get_monitors_list()
        self._monitor_dropdown = ft.Dropdown(
            options=[ft.DropdownOption(m["key"], m["label"]) for m in monitors],
            value=f"Monitor {self._config.monitor_index}",
            bgcolor="#131418",
            border_color="#222329",
            focused_border_color=self._tokens.primary,
            text_size=11.5,
            content_padding=ft.Padding.symmetric(horizontal=10, vertical=6),
            tooltip=monitor_tooltip,
            on_select=lambda e: safe_update(self)
        )

        block_monitor = self._create_setting_block(
            icon=ft.Icons.DESKTOP_WINDOWS_ROUNDED,
            title="Monitor de Captura",
            control=self._monitor_dropdown,
            hint_text="Pantalla donde se ejecuta el juego. El bot capturará y analizará los minijuegos únicamente en este monitor a 60 FPS."
        )

        # ---------------------------------------------------------------------
        # 3. CACHÉ DE TAMAÑO DETECTADO (CPU / RENDIMIENTO)
        # ---------------------------------------------------------------------
        cache_tooltip = (
            "Caché de Tamaño de Botones:\n"
            "Memoriza las dimensiones de los botones y del minijuego tras encontrarlos por primera vez. "
            "Reduce drásticamente el uso de CPU y acelera la tasa de cuadros a 60 FPS continuos (Recomendado: Activado)."
        )

        self._cache_switch = ft.Switch(
            value=self._config.cache_button_size,
            active_color=self._tokens.primary,
            tooltip=cache_tooltip,
            on_change=lambda e: safe_update(self)
        )

        block_cache = self._create_setting_block(
            icon=ft.Icons.BOLT_ROUNDED,
            title="Caché de Dimensiones",
            control=None,
            header_extra=self._cache_switch,
            hint_text="Memoriza la escala geométrica de botones. Reduce el uso de CPU (~85%) para sostener 60 FPS estables."
        )

        # ---------------------------------------------------------------------
        # 4. SENSIBILIDAD DE DETECCIÓN (UMBRAL)
        # ---------------------------------------------------------------------
        thresh_tooltip = (
            "Sensibilidad de Detección (Umbral de confianza):\n"
            "Nivel de precisión visual mínimo requerido para reconocer los botones 'CAST!' y 'REEL!'. "
            "El valor 0.63 es el equilibrio óptimo para evitar clics accidentales y no perder ninguna picada."
        )

        self._thresh_slider = ft.Slider(
            min=0.45,
            max=0.85,
            divisions=40,
            value=self._config.button_threshold,
            label="{value}",
            expand=True,
            active_color=self._tokens.primary,
            inactive_color="#222329",
            tooltip=thresh_tooltip,
            on_change=self._on_slider_change
        )

        self._slider_val_text = ft.Text(
            f"{self._config.button_threshold:.2f}",
            style=ft.TextStyle(
                size=11.5,
                weight=ft.FontWeight.BOLD,
                color="#ffffff",
                font_family="Consolas"
            )
        )
        self._slider_status_text = ft.Text(
            "Óptimo",
            style=ft.TextStyle(
                size=10,
                weight=ft.FontWeight.W_600,
                color=self._tokens.primary
            )
        )
        self._slider_badge = ft.Container(
            content=ft.Row(
                controls=[
                    self._slider_val_text,
                    ft.Container(width=1, height=10, bgcolor="#2e2e38"),
                    self._slider_status_text
                ],
                spacing=5,
                vertical_alignment=ft.CrossAxisAlignment.CENTER
            ),
            padding=ft.Padding.symmetric(horizontal=7, vertical=2),
            border_radius=4,
            bgcolor=self._tokens.badge_bg,
            border=ft.Border.all(1, self._tokens.border_active)
        )
        self._update_slider_badge(self._config.button_threshold)

        block_threshold = self._create_setting_block(
            icon=ft.Icons.TRACK_CHANGES_ROUNDED,
            title="Sensibilidad (Umbral)",
            control=self._thresh_slider,
            header_extra=self._slider_badge,
            hint_text="0.63 es el umbral óptimo probado para reconocer 'CAST!' y 'REEL!' con precisión sin clics en falso."
        )

        # ---------------------------------------------------------------------
        # 5. ENTRADA HUMANIZADA
        # ---------------------------------------------------------------------
        human_tooltip = (
            "Movimiento Humanizado:\n"
            "Genera curvas suaves y variaciones naturales de velocidad al mover el ratón físico en Modo Legacy, "
            "simulando la mano de una persona real."
        )

        self._humanized_switch = ft.Switch(
            value=self._config.humanized_input,
            active_color=self._tokens.primary,
            tooltip=human_tooltip,
            on_change=lambda e: safe_update(self)
        )

        block_humanized = self._create_setting_block(
            icon=ft.Icons.GESTURE_ROUNDED,
            title="Cursor Humanizado",
            control=None,
            header_extra=self._humanized_switch,
            hint_text="Curvas de Bézier suaves con cinemática biológica natural (Aplica solo en Modo Legacy físico)."
        )

        # ---------------------------------------------------------------------
        # 6. ACCIÓN DE GUARDADO
        # ---------------------------------------------------------------------
        save_tooltip = (
            "Guardar Parámetros:\n"
            "Aplica todos los cambios inmediatamente en el bot en tiempo real "
            "y los almacena de forma permanente en config.toml."
        )

        self._save_btn = FletKineticGlowButton(
            text="Guardar Parámetros",
            icon=ft.Icons.SAVE_ROUNDED,
            on_click=self._handle_save,
            width=280,
            is_primary=True,
            confirmed_text="GUARDADOS",
            theme_manager=self._theme_mgr,
            tooltip=save_tooltip
        )

        self._toast_text = ft.Text(
            "",
            style=ft.TextStyle(size=11, weight=ft.FontWeight.W_600, color=self._tokens.primary)
        )

        footer = ft.Container(
            content=ft.Column(
                controls=[
                    self._save_btn,
                    self._toast_text
                ],
                spacing=6,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            ),
            padding=ft.Padding.only(top=4, bottom=4)
        )

        self._theme_mgr.subscribe(self._on_theme_updated)

        super().__init__(
            content=ft.Column(
                controls=[
                    header,
                    block_backend,
                    block_monitor,
                    block_cache,
                    block_threshold,
                    block_humanized,
                    footer
                ],
                spacing=8,
                scroll=ft.ScrollMode.ADAPTIVE
            ),
            expand=True,
            padding=ft.Padding.symmetric(horizontal=6, vertical=4)
        )

    # -------------------------------------------------------------------------
    # BUILDER DE BLOQUES LIMPIOS (SIN REPETICIÓN)
    # -------------------------------------------------------------------------
    def _create_setting_block(
        self,
        icon: str,
        title: str,
        control: ft.Control | None,
        hint_text: str,
        header_extra: ft.Control | None = None
    ) -> ft.Container:
        """Construye un bloque estilizado, compacto y libre de redundancias."""
        icon_box = ft.Container(
            content=ft.Icon(icon, size=14, color=self._tokens.primary),
            width=26,
            height=26,
            border_radius=6,
            bgcolor=self._tokens.accent_subtle,
            border=ft.Border.all(1, self._tokens.border_active),
            alignment=ft.Alignment.CENTER
        )
        self._icon_anchors.append(icon_box)

        title_text = ft.Text(
            title,
            style=ft.TextStyle(
                size=12,
                weight=ft.FontWeight.W_600,
                color="#f1f5f9",
                letter_spacing=0.2
            )
        )

        header_row = ft.Row(
            controls=[
                ft.Row(controls=[icon_box, title_text], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                header_extra if header_extra else ft.Container()
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER
        )

        hint_box = ft.Container(
            content=ft.Text(
                hint_text,
                style=ft.TextStyle(
                    size=10.5,
                    color="#94a3b8",
                    letter_spacing=0.05,
                    height=1.25
                )
            ),
            bgcolor="#141519",
            border=ft.Border(left=ft.BorderSide(3, self._tokens.primary)),
            border_radius=ft.BorderRadius.only(top_right=4, bottom_right=4),
            padding=ft.Padding.symmetric(horizontal=8, vertical=6)
        )
        self._hint_boxes.append(hint_box)

        items: list[ft.Control] = [header_row]
        if control is not None:
            items.append(control)
        items.append(hint_box)

        return ft.Container(
            content=ft.Column(controls=items, spacing=6),
            bgcolor="#0f0f13",
            border=ft.Border.all(1, "#1c1d24"),
            border_radius=8,
            padding=ft.Padding.symmetric(horizontal=10, vertical=8)
        )

    # -------------------------------------------------------------------------
    # HANDLERS Y FEEDBACK EN TIEMPO REAL
    # -------------------------------------------------------------------------
    def _on_backend_change(self, e: ft.ControlEvent) -> None:
        self._update_backend_note(str(self._backend_dropdown.value))
        safe_update(self)

    def _update_backend_note(self, mode: str) -> None:
        m = mode.lower()
        if "postmessage" in m:
            self._backend_active_note.value = "Modo Silencioso (Segundo plano)"
            self._backend_active_note.color = self._tokens.primary
        elif "sendinput" in m:
            self._backend_active_note.value = "Modo Físico Legacy (Cursor Windows)"
            self._backend_active_note.color = "#f59e0b"
        elif "interception" in m:
            self._backend_active_note.value = "Modo Kernel Ring 0"
            self._backend_active_note.color = "#8b5cf6"
        else:
            self._backend_active_note.value = "Modo Simulado (Pruebas)"
            self._backend_active_note.color = "#64748b"

    def _on_slider_change(self, e: ft.ControlEvent) -> None:
        val = round(float(self._thresh_slider.value), 2)
        self._update_slider_badge(val)

    def _update_slider_badge(self, val: float) -> None:
        self._slider_val_text.value = f"{val:.2f}"
        if 0.60 <= val <= 0.66:
            self._slider_status_text.value = "Óptimo"
            self._slider_status_text.color = self._tokens.primary
            self._slider_badge.bgcolor = self._tokens.badge_bg
            self._slider_badge.border = ft.Border.all(1, self._tokens.border_active)
        elif val < 0.60:
            self._slider_status_text.value = "Sensible"
            self._slider_status_text.color = "#f59e0b"
            self._slider_badge.bgcolor = "#1a160d"
            self._slider_badge.border = ft.Border.all(1, "#38290d")
        else:
            self._slider_status_text.value = "Estricto"
            self._slider_status_text.color = "#38bdf8"
            self._slider_badge.bgcolor = "#0e1a24"
            self._slider_badge.border = ft.Border.all(1, "#152e42")
        safe_update(self._slider_badge)

    def _on_theme_updated(self, tokens: ThemeTokens) -> None:
        self._tokens = tokens

        for anchor in self._icon_anchors:
            anchor.content.color = tokens.primary
            anchor.bgcolor = tokens.accent_subtle
            anchor.border = ft.Border.all(1, tokens.border_active)

        for hint_box in self._hint_boxes:
            if hint_box.border and hint_box.border.left:
                hint_box.border.left.color = tokens.primary

        self._backend_dropdown.focused_border_color = tokens.primary
        self._monitor_dropdown.focused_border_color = tokens.primary
        self._cache_switch.active_color = tokens.primary
        self._humanized_switch.active_color = tokens.primary
        self._thresh_slider.active_color = tokens.primary

        self._update_slider_badge(round(float(self._thresh_slider.value), 2))
        self._update_backend_note(str(self._backend_dropdown.value))

        if "guardados" in str(self._toast_text.value).lower():
            self._toast_text.style.color = tokens.primary

        safe_update(self)

    def _get_monitors_list(self) -> list[dict[str, str]]:
        monitors = []
        try:
            with mss.MSS() as sct:
                for i in range(1, len(sct.monitors)):
                    m = sct.monitors[i]
                    monitors.append({
                        "key": f"Monitor {i}",
                        "label": f"Monitor {i} ({m['width']}x{m['height']})"
                    })
        except Exception:
            monitors.append({"key": "Monitor 1", "label": "Monitor 1 (1920x1080)"})
        return monitors

    def _handle_save(self) -> None:
        try:
            m = re.search(r"Monitor\s+(\d+)", str(self._monitor_dropdown.value))
            mon_idx = int(m.group(1)) if m else 1

            updated = AppConfig(
                target_fps=self._config.target_fps,
                input_backend=str(self._backend_dropdown.value),
                vision_strategy=self._config.vision_strategy,
                capture_source=self._config.capture_source,
                monitor_index=mon_idx,
                button_threshold=round(float(self._thresh_slider.value), 2),
                cache_button_size=bool(self._cache_switch.value),
                humanized_input=bool(self._humanized_switch.value),
                ui_theme=self._config.ui_theme,
                ui_transparency=self._config.ui_transparency
            )
            self._config = updated
            save_config(updated, self._config_path)

            if self._on_save_cb:
                self._on_save_cb(updated)

            self._toast_text.value = "Parámetros guardados y aplicados."
            self._toast_text.style.color = self._tokens.primary
            safe_update(self)
        except Exception as exc:
            self._toast_text.value = f"Error: {exc}"
            self._toast_text.style.color = "#ef4444"
            safe_update(self)
