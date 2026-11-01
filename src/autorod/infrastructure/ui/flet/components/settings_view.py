"""Vista de Configuración de Parámetros en Flet."""

from typing import Callable, Any
import flet as ft
from autorod.infrastructure.ui.flet.theme import ThemeManager, ThemeTokens
from autorod.config import AppConfig, save_config
from autorod.infrastructure.ui.flet.components.kinetic_button import FletKineticGlowButton
from autorod.infrastructure.ui.flet.utils import safe_update
import mss


class FletSettingsView(ft.Container):
    """Panel de configuración de parámetros de captura y visión."""

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
                    ft.Text("Ajusta los dispositivos de captura de pantalla, algoritmos y sensibilidad en caliente.", size=12, color="#9ca3af")
                ],
                spacing=3
            ),
            bgcolor="#11131c",
            border=ft.Border.all(1, "#1e2232"),
            border_radius=10,
            padding=ft.Padding.symmetric(horizontal=16, vertical=12)
        )

        monitors = self._get_monitors_list()
        self._monitor_dropdown = ft.Dropdown(
            label="Monitor Físico de Captura",
            options=[ft.DropdownOption(m["key"], m["label"]) for m in monitors],
            value=f"Monitor {self._config.monitor_index}",
            width=320,
            bgcolor="#141622",
            border_color="#25293d"
        )

        self._cache_switch = ft.Switch(
            label="Guardar tamaño detectado (Mínimo uso de CPU/RAM - Recomendado)",
            value=self._config.cache_button_size,
            active_color=self._theme_mgr.current.primary
        )

        self._thresh_slider = ft.Slider(
            min=0.45,
            max=0.85,
            divisions=40,
            value=self._config.button_threshold,
            label="{value}",
            expand=True
        )

        self._backend_dropdown = ft.Dropdown(
            label="Simulador de Hardware",
            options=[
                ft.DropdownOption("sendinput", "SendInput (Nativo Windows)"),
                ft.DropdownOption("interception", "Interception (Driver Ring 0)"),
                ft.DropdownOption("fake", "Modo Simulado (Pruebas)")
            ],
            value=self._config.input_backend,
            width=320,
            bgcolor="#141622",
            border_color="#25293d"
        )

        self._save_btn = FletKineticGlowButton(
            text="💾 Guardar Parámetros",
            on_click=self._handle_save,
            width=190,
            is_primary=True,
            confirmed_text="✓ GUARDADOS",
            theme_manager=self._theme_mgr
        )

        self._toast_text = ft.Text("", size=12, weight=ft.FontWeight.BOLD, color=self._theme_mgr.current.primary)

        form_panel = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("Dispositivos de Entrada e Ingesta", size=13, weight=ft.FontWeight.BOLD, color="#ffffff"),
                    self._monitor_dropdown,
                    ft.Divider(color="#1c1f2b", height=12),
                    ft.Text("Optimización y Rendimiento", size=13, weight=ft.FontWeight.BOLD, color="#ffffff"),
                    self._cache_switch,
                    ft.Divider(color="#1c1f2b", height=12),
                    ft.Text("Sensibilidad de Detección de Botones (0.63 recomendado):", size=12, color="#9ca3af"),
                    self._thresh_slider,
                    ft.Divider(color="#1c1f2b", height=12),
                    ft.Text("Backend de Simulación:", size=12, color="#9ca3af"),
                    self._backend_dropdown,
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
                humanized_input=self._config.humanized_input,
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
