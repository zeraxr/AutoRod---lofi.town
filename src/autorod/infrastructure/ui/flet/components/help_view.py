"""Vista de Ayuda, Guías y Soporte en Flet (Diseño Oficial Figma 1:1)."""

import webbrowser
from typing import Any
import flet as ft
from autorod.infrastructure.ui.flet.theme import ThemeManager, ThemeTokens
from autorod.infrastructure.ui.flet.utils import safe_update


class FletHelpView(ft.Container):
    """
    Panel de Ayuda, solución de problemas y soporte comunitario.
    Estrictamente alineado 1:1 con Figma (Frames 72:5056 Modo Oscuro y 78:803 Modo Claro).
    """

    def __init__(self, theme_manager: ThemeManager | None = None) -> None:
        self._theme_mgr = theme_manager or ThemeManager.get_instance()
        self._tokens: ThemeTokens = self._theme_mgr.current

        # ---------------------------------------------------------------------
        # 0. HEADER PRINCIPAL (Figma 72:5056)
        # ---------------------------------------------------------------------
        self._title_text = ft.Text(
            "Ayuda y Soporte",
            size=26,
            weight=ft.FontWeight.W_700,
            color=self._tokens.text_primary
        )
        self._subtitle_text = ft.Text(
            "Guías de inicio rápido, preguntas frecuentes y soporte comunitario.",
            size=12,
            color=self._tokens.text_secondary
        )

        header = ft.Row(
            controls=[
                ft.Column(
                    controls=[self._title_text, self._subtitle_text],
                    spacing=2
                ),
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.HELP_OUTLINE_ROUNDED, size=14, color=self._tokens.primary),
                            ft.Text("V2.0 OFICIAL", size=10, weight=ft.FontWeight.W_700, color=self._tokens.primary)
                        ],
                        spacing=6
                    ),
                    bgcolor=self._tokens.sub_bg,
                    border=ft.Border.all(1, self._tokens.card_border),
                    border_radius=6,
                    padding=ft.Padding.symmetric(horizontal=10, vertical=6)
                )
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER
        )

        # ---------------------------------------------------------------------
        # 1. BARRA DE BÚSQUEDA RÁPIDA (Figma 72:5056)
        # ---------------------------------------------------------------------
        self._search_input = ft.TextField(
            hint_text="Buscar en las guías y preguntas frecuentes...",
            hint_style=ft.TextStyle(size=12, color=self._tokens.text_muted),
            text_size=12,
            border_radius=10,
            border_color=self._tokens.card_border,
            focused_border_color=self._tokens.primary,
            bgcolor=self._tokens.card_bg,
            color=self._tokens.text_primary,
            content_padding=ft.Padding.symmetric(horizontal=14, vertical=10),
            prefix_icon=ft.Icons.SEARCH_ROUNDED,
            suffix=ft.Container(
                content=ft.Text("Ctrl + K", size=10, weight=ft.FontWeight.BOLD, color=self._tokens.text_secondary),
                bgcolor=self._tokens.sub_bg,
                border=ft.Border.all(1, self._tokens.card_border),
                border_radius=4,
                padding=ft.Padding.symmetric(horizontal=6, vertical=2)
            ),
            expand=True,
            on_change=self._on_search_query
        )

        search_bar = ft.Container(
            content=self._search_input,
            margin=ft.Margin.only(bottom=6)
        )

        # ---------------------------------------------------------------------
        # 2. TU PRIMERA SESIÓN EN 3 PASOS (Figma 72:5056)
        # ---------------------------------------------------------------------
        def _create_step_card(step_num: str, title: str, description: str) -> ft.Container:
            return ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text(step_num, size=20, weight=ft.FontWeight.BOLD, color=self._tokens.primary),
                        ft.Text(title, size=13, weight=ft.FontWeight.W_600, color=self._tokens.text_primary),
                        ft.Text(description, size=11, color=self._tokens.text_secondary)
                    ],
                    spacing=4
                ),
                bgcolor=self._tokens.card_bg,
                border=ft.Border.all(1, self._tokens.card_border),
                border_radius=12,
                padding=14,
                expand=True
            )

        steps_row = ft.Row(
            controls=[
                _create_step_card(
                    "01",
                    "Elige tu pantalla",
                    "Selecciona el monitor donde está abierto el juego en la pestaña Configuración."
                ),
                _create_step_card(
                    "02",
                    "Ajusta el objetivo",
                    "Calibra la confianza mínima en Parámetros según la iluminación de tu pantalla."
                ),
                _create_step_card(
                    "03",
                    "Empieza a pescar",
                    "Presiona F8 o el botón Iniciar en el panel principal. Usa Q para emergencia."
                ),
            ],
            spacing=12
        )

        steps_section = ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.ROCKET_LAUNCH_ROUNDED, size=16, color=self._tokens.primary),
                        ft.Text("Tu primera sesión en 3 pasos", size=14, weight=ft.FontWeight.W_600, color=self._tokens.text_primary)
                    ],
                    spacing=8
                ),
                steps_row
            ],
            spacing=10
        )

        # ---------------------------------------------------------------------
        # 3. PREGUNTAS FRECUENTES (FAQ) (Figma 72:5056)
        # ---------------------------------------------------------------------
        self._faq_data = [
            (
                "¿Cómo evito que se pause al cambiar de ventana?",
                "En la pestaña Configuración, desactiva el interruptor 'Pausar al cambiar de ventana'. De este modo, AutoRod continuará pescando de forma autónoma mientras navegas o trabajas en otras aplicaciones."
            ),
            (
                "¿Por qué no detecta el anzuelo correctamente?",
                "Verifica que el monitor seleccionado en Configuración coincida con la pantalla del juego. Si hay variaciones de luz o lluvia en el juego, ve a Parámetros y ajusta la 'Tolerancia de color' al 25% o disminuye la 'Confianza mínima' al 75%."
            ),
            (
                "¿Es seguro usar AutoRod en segundo plano?",
                "Sí, completamente. AutoRod opera mediante captura visual no intrusiva con MSS y emulación de clics del sistema operativo. No inyecta DLLs ni altera la memoria de ningún proceso."
            ),
            (
                "¿Qué atajos de teclado globales existen?",
                "• F8: Inicia o pausa la sesión activa inmediatamente.\n• F9: Detiene la sesión por completo y resetea estadísticas.\n• Q / Alt+Q: Parada de emergencia instantánea e incondicional a nivel de sistema operativo."
            )
        ]

        self._faq_containers: list[ft.Container] = []
        for q, a in self._faq_data:
            c = ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.HELP_OUTLINE_ROUNDED, size=14, color=self._tokens.primary),
                                ft.Text(q, size=12.5, weight=ft.FontWeight.W_600, color=self._tokens.text_primary, expand=True)
                            ],
                            spacing=8
                        ),
                        ft.Text(a, size=11.5, color=self._tokens.text_secondary)
                    ],
                    spacing=6
                ),
                bgcolor=self._tokens.card_bg,
                border=ft.Border.all(1, self._tokens.card_border),
                border_radius=10,
                padding=12
            )
            self._faq_containers.append(c)

        faq_section = ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.QUESTION_ANSWER_ROUNDED, size=16, color=self._tokens.primary),
                        ft.Text("Preguntas Frecuentes", size=14, weight=ft.FontWeight.W_600, color=self._tokens.text_primary)
                    ],
                    spacing=8
                ),
                ft.Column(controls=self._faq_containers, spacing=8)
            ],
            spacing=10
        )

        # ---------------------------------------------------------------------
        # 4. COMUNIDAD Y SOPORTE OFICIAL (Figma 72:5056)
        # ---------------------------------------------------------------------
        self._discord_btn = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.FORUM_ROUNDED, size=14, color=self._tokens.text_on_primary),
                    ft.Text("Unirse a Discord", size=12, color=self._tokens.text_on_primary, weight=ft.FontWeight.W_600)
                ],
                spacing=6,
                alignment=ft.MainAxisAlignment.CENTER
            ),
            bgcolor=self._tokens.primary,
            border_radius=8,
            height=36,
            padding=ft.Padding.symmetric(horizontal=16),
            on_click=lambda _: webbrowser.open("https://discord.gg/autorod"),
            ink=True
        )

        support_card = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Icon(ft.Icons.DISCORD_ROUNDED if hasattr(ft.Icons, "DISCORD_ROUNDED") else ft.Icons.FORUM_ROUNDED, size=18, color=self._tokens.primary),
                                    ft.Text("Comunidad y Soporte Oficial", size=14, weight=ft.FontWeight.W_600, color=self._tokens.text_primary)
                                ],
                                spacing=8
                            ),
                            ft.Text(
                                "¿Tienes dudas, sugerencias o necesitas perfiles para otros juegos? Únete a nuestra comunidad oficial.",
                                size=11.5,
                                color=self._tokens.text_secondary
                            )
                        ],
                        spacing=4,
                        expand=True
                    ),
                    self._discord_btn
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER
            ),
            bgcolor=self._tokens.card_bg,
            border=ft.Border.all(1, self._tokens.card_border),
            border_radius=12,
            padding=16
        )

        # ---------------------------------------------------------------------
        # 5. FOOTER
        # ---------------------------------------------------------------------
        footer = ft.Row(
            controls=[
                ft.Text("AutoRod v2.0-SOTA · Documentación y Guías", size=11, color=self._tokens.text_muted),
                ft.Text("Licencia Abierta MIT", size=11, color=self._tokens.text_muted)
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        )

        content_column = ft.Column(
            controls=[
                header,
                search_bar,
                steps_section,
                faq_section,
                support_card,
                footer
            ],
            spacing=16,
            scroll=ft.ScrollMode.ADAPTIVE
        )

        super().__init__(
            content=content_column,
            padding=ft.Padding.all(20),
            bgcolor=self._tokens.canvas_bg,
            border_radius=ft.BorderRadius.only(top_left=16, bottom_left=16),
            expand=True
        )

    def _on_search_query(self, e: Any) -> None:
        q = (self._search_input.value or "").strip().lower()
        for idx, (question, answer) in enumerate(self._faq_data):
            matched = (q in question.lower()) or (q in answer.lower()) or (q == "")
            self._faq_containers[idx].visible = matched
        safe_update(self)

    def apply_theme(self, tokens: ThemeTokens) -> None:
        self._tokens = tokens
        self.bgcolor = tokens.canvas_bg
        self._title_text.color = tokens.text_primary
        self._subtitle_text.color = tokens.text_secondary
        self._search_input.bgcolor = tokens.card_bg
        self._search_input.border_color = tokens.card_border
        self._search_input.color = tokens.text_primary
        self._discord_btn.bgcolor = tokens.primary
        safe_update(self)
