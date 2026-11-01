"""Skeleton Loader moderno para AutoRod durante la carga inicial del motor."""

from pathlib import Path
import flet as ft
from autorod.infrastructure.ui.flet.theme import ThemeManager, ThemeTokens
from autorod.infrastructure.ui.flet.utils import safe_update


class FletDashboardSkeleton(ft.Container):
    """
    Vista de carga tipo Skeleton Screen que emula la geometría exacta del Dashboard.
    Proporciona retroalimentación visual inmediata con animaciones de pulso y shimmer
    mientras se inicializa la ingesta de video MSS y el motor de visión.
    """

    def __init__(
        self,
        theme_manager: ThemeManager | None = None
    ) -> None:
        self._theme_mgr = theme_manager or ThemeManager.get_instance()
        self._theme: ThemeTokens = self._theme_mgr.current

        # 1. Shimmer blocks del HUD superior
        self._hud_status = ft.Container(
            width=150,
            height=14,
            border_radius=4,
            bgcolor="#202024",
            animate=ft.Animation(750, ft.AnimationCurve.EASE_IN_OUT)
        )
        self._hud_res = ft.Container(
            width=90,
            height=14,
            border_radius=4,
            bgcolor="#18181b",
            animate=ft.Animation(750, ft.AnimationCurve.EASE_IN_OUT)
        )
        self._hud_mode = ft.Container(
            width=110,
            height=14,
            border_radius=4,
            bgcolor="#1c1c20",
            animate=ft.Animation(750, ft.AnimationCurve.EASE_IN_OUT)
        )

        hud_skeleton = ft.Container(
            content=ft.Row(
                controls=[
                    self._hud_status,
                    ft.Row(controls=[self._hud_mode, self._hud_res], spacing=12)
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
            ),
            padding=ft.Padding.symmetric(horizontal=14, vertical=9),
            bgcolor="#0e0e11",
            border_radius=8,
            border=ft.Border.all(1, "#1c1c20"),
            margin=ft.Margin.only(bottom=6)
        )

        # 2. Viewport Canvas Central con radar/spinner de carga y pasos diagnósticos
        self._spinner = ft.ProgressRing(
            width=38,
            height=38,
            stroke_width=3.5,
            color=self._theme.primary
        )

        badge_mss = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Container(width=6, height=6, border_radius=3, bgcolor="#10b981"),
                    ft.Text("MSS CAPTURE", size=10, weight=ft.FontWeight.BOLD, color="#a1a1aa")
                ],
                spacing=5
            ),
            padding=ft.Padding.symmetric(horizontal=8, vertical=4),
            bgcolor="#141417",
            border_radius=6,
            border=ft.Border.all(1, "#222226")
        )

        badge_vision = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Container(width=6, height=6, border_radius=3, bgcolor="#38bdf8"),
                    ft.Text("VISIÓN ADAPTATIVA O(1)", size=10, weight=ft.FontWeight.BOLD, color="#a1a1aa")
                ],
                spacing=5
            ),
            padding=ft.Padding.symmetric(horizontal=8, vertical=4),
            bgcolor="#141417",
            border_radius=6,
            border=ft.Border.all(1, "#222226")
        )

        badge_input = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Container(width=6, height=6, border_radius=3, bgcolor="#64748b"),
                    ft.Text("HARDWARE SIMULATOR", size=10, weight=ft.FontWeight.BOLD, color="#a1a1aa")
                ],
                spacing=5
            ),
            padding=ft.Padding.symmetric(horizontal=8, vertical=4),
            bgcolor="#141417",
            border_radius=6,
            border=ft.Border.all(1, "#222226")
        )

        icons_dir = Path(__file__).resolve().parents[3] / "assets" / "icons"
        logo_path = icons_dir / "logo_48.png"
        if not logo_path.is_file():
            logo_path = icons_dir / "logo.png"

        logo_image = ft.Image(
            src=str(logo_path),
            width=48,
            height=48,
            fit=ft.BoxFit.CONTAIN
        )

        viewport_skeleton = ft.Container(
            content=ft.Column(
                controls=[
                    hud_skeleton,
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                logo_image,
                                self._spinner,
                                ft.Text(
                                    "INICIALIZANDO MOTOR AUTOROD",
                                    size=13,
                                    weight=ft.FontWeight.BOLD,
                                    color="#f8fafc"
                                ),
                                ft.Text(
                                    "Sincronizando flujo de video a 60 FPS y calibrando plantillas...",
                                    size=11,
                                    color="#71717a"
                                ),
                                ft.Container(height=10),
                                ft.Row(
                                    controls=[badge_mss, badge_vision, badge_input],
                                    spacing=8,
                                    alignment=ft.MainAxisAlignment.CENTER
                                )
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=6
                        ),
                        alignment=ft.Alignment(0, 0),
                        expand=True,
                        bgcolor="#08080a",
                        border_radius=10,
                        border=ft.Border.all(1, "#1c1c20")
                    )
                ],
                expand=True
            ),
            expand=True,
            bgcolor="#121214",
            border=ft.Border.all(1, "#222225"),
            border_radius=12,
            padding=ft.Padding.all(8)
        )

        # 3. 4 Tarjetas Métricas Skeleton
        self._metric_skeletons: list[ft.Container] = []
        metric_controls: list[ft.Control] = []

        titles = ["ESTADO DEL MOTOR", "CACHÉ DE TAMAÑO", "MONITOR CAPTURA", "LATENCIA ESTIMADA"]
        for t in titles:
            card = ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text(t, size=10, weight=ft.FontWeight.BOLD, color="#71717a"),
                        ft.Container(
                            width=100,
                            height=20,
                            border_radius=4,
                            bgcolor="#202024",
                            animate=ft.Animation(750, ft.AnimationCurve.EASE_IN_OUT)
                        ),
                        ft.Container(
                            width=70,
                            height=10,
                            border_radius=3,
                            bgcolor="#18181b",
                            animate=ft.Animation(750, ft.AnimationCurve.EASE_IN_OUT)
                        )
                    ],
                    spacing=6
                ),
                bgcolor="#121214",
                border=ft.Border.all(1, "#222225"),
                border_radius=10,
                padding=ft.Padding.all(12),
                expand=True
            )
            self._metric_skeletons.append(card)
            metric_controls.append(card)

        cards_skeleton_row = ft.Row(controls=metric_controls, spacing=8)

        super().__init__(
            content=ft.Column(
                controls=[
                    viewport_skeleton,
                    cards_skeleton_row
                ],
                spacing=8,
                expand=True
            ),
            expand=True,
            padding=ft.Padding.all(10),
            bgcolor="#080809"
        )

        self._theme_mgr.subscribe(self._on_theme_updated)

    def _on_theme_updated(self, tokens: ThemeTokens) -> None:
        self._theme = tokens
        self._spinner.color = tokens.primary
        safe_update(self)
