"""Vista de Configuración de Parámetros en Flet."""

from typing import Callable, Any
import flet as ft
from autorod.infrastructure.ui.flet.theme import ThemeManager, ThemeTokens
from autorod.config import AppConfig, save_config
from autorod.infrastructure.ui.flet.components.kinetic_button import FletKineticGlowButton
from autorod.infrastructure.ui.flet.utils import safe_update
import mss


class FletSettingsView(ft.Container):
    """
    Panel de configuración de parámetros de captura, visión e inyección de hardware.
    Cada opción dispone de leyendas explicativas interactivas (Tooltips) directas y simples.
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

        header = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("⚙️ Parámetros de Ejecución y Captura Física", size=18, weight=ft.FontWeight.BOLD, color="#ffffff"),
                    ft.Text("Pasa el ratón sobre cualquier opción para ver una explicación simple de su funcionamiento.", size=12, color="#9ca3af")
                ],
                spacing=3
            ),
            bgcolor="#11131c",
            border=ft.Border.all(1, "#1e2232"),
            border_radius=10,
            padding=ft.Padding.symmetric(horizontal=16, vertical=12)
        )

        # 1. Modo de Clics (Legacy vs Nuevo)
        backend_tooltip = (
            "Modo de Clics (Simulador):\n"
            "• Modo Nuevo (PostMessage): Inyecta clics silenciosos en segundo plano sin mover el ratón físico de Windows. "
            "Ideal para trabajar, programar o navegar en tu monitor principal mientras pesca en el secundario.\n"
            "• Modo Legacy (SendInput): Mueve físicamente el cursor de Windows en la pantalla para hacer clic."
        )
        self._backend_dropdown = ft.Dropdown(
            label="Modo de Clics y Simulación",
            options=[
                ft.DropdownOption("postmessage", "⭐ Modo Nuevo: Silencioso (Sin mover el ratón)"),
                ft.DropdownOption("sendinput", "Modo Legacy: Físico (Mueve el cursor de Windows)"),
                ft.DropdownOption("interception", "Modo Conductor Kernel: Ring 0 (Interception)"),
                ft.DropdownOption("fake", "Modo Pruebas: Simulado (Sin clics reales)")
            ],
            value=self._config.input_backend,
            width=360,
            bgcolor="#141622",
            border_color="#25293d",
            tooltip=backend_tooltip
        )

        # 2. Monitor Físico de Captura
        monitor_tooltip = (
            "Monitor Físico de Captura:\n"
            "Selecciona la pantalla donde está abierto el juego. "
            "El bot capturará y analizará los minijuegos únicamente en este monitor."
        )
        monitors = self._get_monitors_list()
        self._monitor_dropdown = ft.Dropdown(
            label="Monitor Físico de Captura",
            options=[ft.DropdownOption(m["key"], m["label"]) for m in monitors],
            value=f"Monitor {self._config.monitor_index}",
            width=360,
            bgcolor="#141622",
            border_color="#25293d",
            tooltip=monitor_tooltip
        )

        # 3. Guardar tamaño detectado (Caché de resolución)
        cache_tooltip = (
            "Caché de Tamaño de Botones:\n"
            "Memoriza las dimensiones de los botones y del minijuego tras encontrarlos por primera vez. "
            "Reduce drásticamente el uso de CPU y acelera la tasa de cuadros a 60 FPS continuos (Recomendado: Activado)."
        )
        self._cache_switch = ft.Switch(
            label="Guardar tamaño detectado (Mínimo uso de CPU/RAM - Recomendado)",
            value=self._config.cache_button_size,
            active_color=self._theme_mgr.current.primary,
            tooltip=cache_tooltip
        )

        # 4. Sensibilidad de Detección de Botones
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
            tooltip=thresh_tooltip
        )

        # 5. Entrada Humanizada (Curvas de Bézier)
        human_tooltip = (
            "Movimiento Humanizado:\n"
            "Genera curvas suaves y variaciones naturales de velocidad al mover el ratón físico en Modo Legacy, "
            "simulando la mano de una persona real."
        )
        self._humanized_switch = ft.Switch(
            label="Movimiento con trayectoria humana natural (Solo Modo Legacy)",
            value=self._config.humanized_input,
            active_color=self._theme_mgr.current.primary,
            tooltip=human_tooltip
        )

        # 6. Botón de Guardado
        save_tooltip = (
            "Guardar Parámetros:\n"
            "Aplica todos los cambios inmediatamente en el bot en tiempo real "
            "y los almacena de forma permanente en config.toml."
        )
        self._save_btn = FletKineticGlowButton(
            text="💾 Guardar Parámetros",
            on_click=self._handle_save,
            width=210,
            is_primary=True,
            confirmed_text="✓ GUARDADOS",
            theme_manager=self._theme_mgr,
            tooltip=save_tooltip
        )

        self._toast_text = ft.Text("", size=12, weight=ft.FontWeight.BOLD, color=self._theme_mgr.current.primary)

        # Helpers para encabezados con icono de ayuda informativo
        def _setting_section(title: str, tip: str, control: ft.Control, subtitle: str | None = None) -> ft.Column:
            row_items: list[ft.Control] = [
                ft.Text(title, size=13, weight=ft.FontWeight.BOLD, color="#ffffff", tooltip=tip),
                ft.Icon(ft.Icons.HELP_OUTLINE_ROUNDED, size=15, color="#6b7280", tooltip=tip)
            ]
            items: list[ft.Control] = [
                ft.Row(controls=row_items, spacing=6, vertical_alignment=ft.CrossAxisAlignment.CENTER)
            ]
            if subtitle:
                items.append(ft.Text(subtitle, size=11, color="#9ca3af", tooltip=tip))
            items.append(control)
            return ft.Column(controls=items, spacing=6)

        form_panel = ft.Container(
            content=ft.Column(
                controls=[
                    _setting_section(
                        "Modo de Inyección de Clics",
                        backend_tooltip,
                        self._backend_dropdown,
                        "Alterna entre inyección en segundo plano (Modo Nuevo) o física de cursor (Modo Legacy)."
                    ),
                    ft.Divider(color="#1c1f2b", height=12),
                    _setting_section(
                        "Dispositivo de Ingesta Visual",
                        monitor_tooltip,
                        self._monitor_dropdown,
                        "Pantalla donde está ubicado el juego a monitorear."
                    ),
                    ft.Divider(color="#1c1f2b", height=12),
                    _setting_section(
                        "Optimización y Rendimiento de CPU",
                        cache_tooltip,
                        self._cache_switch,
                        "Evita re-escanear múltiples escalas por fotograma una vez localizado el dial."
                    ),
                    ft.Divider(color="#1c1f2b", height=12),
                    _setting_section(
                        "Sensibilidad de Detección de Botones (0.63 recomendado)",
                        thresh_tooltip,
                        self._thresh_slider,
                        "Umbral de coincidencia matemática para 'CAST!' y 'REEL!'."
                    ),
                    ft.Divider(color="#1c1f2b", height=12),
                    _setting_section(
                        "Comportamiento de Cursor Humano",
                        human_tooltip,
                        self._humanized_switch,
                        "Trayectorias no lineales para evasión de detección heurística."
                    ),
                    ft.Container(height=8),
                    ft.Row(controls=[self._save_btn, self._toast_text], spacing=16)
                ],
                spacing=10
            ),
            bgcolor="#11131c",
            border=ft.Border.all(1, "#1e2232"),
            border_radius=10,
            padding=ft.Padding.all(16)
        )

        super().__init__(
            content=ft.Column(
                controls=[
                    header,
                    form_panel
                ],
                spacing=12,
                scroll=ft.ScrollMode.ADAPTIVE
            ),
            expand=True,
            padding=ft.Padding.all(14)
        )

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
            import re
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

            self._toast_text.value = "✓ Parámetros guardados y aplicados."
            self._toast_text.color = self._theme_mgr.current.primary
            safe_update(self)
        except Exception as exc:
            self._toast_text.value = f"Error: {exc}"
            self._toast_text.color = "#ef4444"
            safe_update(self)
