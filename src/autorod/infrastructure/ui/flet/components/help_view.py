"""Vista de Ayuda, Guías y Soporte en Flet (Diseño Oficial Figma 1:1)."""

import platform
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
        # 0. HEADER PRINCIPAL (Figma 72:5141)
        # ---------------------------------------------------------------------
        self._title_text = ft.Text(
            "Ayuda",
            size=29,
            weight=ft.FontWeight.W_600,
            color="#ffffff" if self._tokens.mode == "dark" else self._tokens.text_primary
        )
        self._subtitle_text = ft.Text(
            "Menos dudas, más pesca :3",
            size=13,
            weight=ft.FontWeight.NORMAL,
            color="#a5b4ff" if self._tokens.mode == "dark" else self._tokens.text_secondary
        )

        presentation_header = ft.Column(
            controls=[self._title_text, self._subtitle_text],
            spacing=8
        )

        # ---------------------------------------------------------------------
        # 1. BARRA DE BÚSQUEDA RÁPIDA (Figma 72:5145)
        # ---------------------------------------------------------------------
        self._search_input = ft.TextField(
            hint_text="Buscar en guías y preguntas frecuentes…",
            hint_style=ft.TextStyle(size=12, color="#8f99b3" if self._tokens.mode == "dark" else "#9ca3af"),
            text_size=12,
            border=None,
            border_color=ft.Colors.TRANSPARENT,
            content_padding=ft.Padding.symmetric(horizontal=8, vertical=10),
            color="#ffffff" if self._tokens.mode == "dark" else self._tokens.text_primary,
            expand=True,
            on_change=self._on_search_query
        )

        self._search_icon = ft.Icon(ft.Icons.SEARCH_ROUNDED, size=16, color="#8f99b3")
        self._search_shortcut_badge = ft.Text(
            "Ctrl + K",
            size=10,
            weight=ft.FontWeight.NORMAL,
            color="#8f99b3"
        )

        search_bg = "#0d0f17" if self._tokens.mode == "dark" else "#f9fafb"
        search_border = "#2a2f3a" if self._tokens.mode == "dark" else "#e5e7eb"
        self._search_bar_frame = ft.Container(
            content=ft.Row(
                controls=[
                    self._search_icon,
                    self._search_input,
                    self._search_shortcut_badge
                ],
                spacing=10,
                vertical_alignment=ft.CrossAxisAlignment.CENTER
            ),
            height=42,
            padding=ft.Padding.symmetric(horizontal=14),
            border_radius=8,
            bgcolor=search_bg,
            border=ft.Border.all(1, search_border)
        )

        # ---------------------------------------------------------------------
        # 2. TU PRIMERA SESIÓN EN 3 PASOS (Figma 72:5149)
        # ---------------------------------------------------------------------
        self._steps_title = ft.Text(
            "Tu primera sesión",
            size=14,
            weight=ft.FontWeight.W_600,
            color="#ffffff" if self._tokens.mode == "dark" else self._tokens.text_primary
        )
        self._steps_subtitle = ft.Text(
            "Tres pasos para dejar AutoRod preparado.",
            size=11,
            color="#8f99b3" if self._tokens.mode == "dark" else "#6b7280"
        )

        def _create_step(num: str, title: str, desc: str) -> ft.Container:
            return ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text(num, size=11, weight=ft.FontWeight.W_600, color="#a5b4ff"),
                        ft.Text(title, size=13, weight=ft.FontWeight.W_600, color="#ffffff" if self._tokens.mode == "dark" else self._tokens.text_primary),
                        ft.Text(desc, size=11, color="#8f99b3" if self._tokens.mode == "dark" else "#6b7280")
                    ],
                    spacing=9
                ),
                expand=True
            )

        self._step1 = _create_step("01", "Elige tu pantalla", "Selecciona Monitor 1 en Configuración.")
        self._step2 = _create_step("02", "Ajusta el objetivo", "Usa el perfil equilibrado en Parámetros.")
        self._step3 = _create_step("03", "Empieza a pescar", "Abre el juego y pulsa iniciar o Shift + Q.")

        steps_row = ft.Row(
            controls=[self._step1, self._step2, self._step3],
            spacing=20
        )

        card_bg = "#0d0f17" if self._tokens.mode == "dark" else "#ffffff"
        card_border = "#1b2233" if self._tokens.mode == "dark" else "#e5e7eb"

        self._steps_card = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Column(
                        controls=[self._steps_title, self._steps_subtitle],
                        spacing=5
                    ),
                    steps_row
                ],
                spacing=12
            ),
            bgcolor=card_bg,
            border=ft.Border.all(1, card_border),
            border_radius=12,
            padding=16
        )

        # ---------------------------------------------------------------------
        # 3. PREGUNTAS FRECUENTES (FAQ) (Figma 72:5167)
        # ---------------------------------------------------------------------
        self._faq_title = ft.Text(
            "Preguntas frecuentes",
            size=14,
            weight=ft.FontWeight.W_600,
            color="#ffffff" if self._tokens.mode == "dark" else self._tokens.text_primary
        )

        self._faq_data = [
            (
                "¿Por qué aparece «Esperando objetivo»?",
                "La caché se prepara cuando AutoRod detecta el objetivo. Comprueba que el juego esté visible en Monitor 1 y reanuda la sesión. Si no lo encuentra, revisa el área de búsqueda y la confianza mínima en Parámetros."
            ),
            (
                "¿Cómo evito que se pause al cambiar de ventana?",
                "En la pestaña Configuración, desactiva el interruptor 'Pausar al cambiar de ventana'. De este modo, AutoRod continuará pescando de forma autónoma mientras navegas o trabajas en otras aplicaciones."
            ),
            (
                "La captura va lenta, ¿qué puedo hacer?",
                "Asegúrate de ejecutar el juego en modo ventana o sin bordes y comprueba los FPS en Configuración. Nota: Opera GX no funciona bien porque limita los recursos de CPU necesarios para el reconocimiento del bot."
            ),
            (
                "¿Cómo pauso la pesca de inmediato?",
                "Puedes pulsar el atajo global Shift + Q en cualquier momento para pausar o reanudar, o hacer clic en el botón pausar en la pantalla de Inicio. Para cerrar la aplicación por completo, pulsa Alt + Q."
            )
        ]

        self._faq_containers: list[ft.Container] = []
        self._faq_expanded_states: list[bool] = [True, False, False, False]
        self._faq_answer_texts: list[ft.Text] = []
        self._faq_chevron_icons: list[ft.Icon] = []

        for idx, (q, a) in enumerate(self._faq_data):
            is_expanded = self._faq_expanded_states[idx]

            chevron = ft.Icon(
                ft.Icons.KEYBOARD_ARROW_UP_ROUNDED if is_expanded else ft.Icons.KEYBOARD_ARROW_DOWN_ROUNDED,
                size=16,
                color="#8f99b3"
            )
            self._faq_chevron_icons.append(chevron)

            q_text = ft.Text(
                q,
                size=13 if idx == 0 else 12,
                weight=ft.FontWeight.NORMAL,
                color="#ffffff" if self._tokens.mode == "dark" else self._tokens.text_primary,
                expand=True
            )

            a_text = ft.Text(
                a,
                size=12,
                color="#8f99b3" if self._tokens.mode == "dark" else "#6b7280",
                visible=is_expanded
            )
            self._faq_answer_texts.append(a_text)

            q_row = ft.Row(
                controls=[q_text, chevron],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER
            )

            item_col = ft.Column(
                controls=[q_row, a_text],
                spacing=8
            )

            border_top = None if idx == 0 else ft.Border(top=ft.BorderSide(1, card_border))
            pt = 0 if idx == 0 else 12

            item_container = ft.Container(
                content=item_col,
                border=border_top,
                padding=ft.Padding.only(top=pt),
                on_click=lambda e, i=idx: self._toggle_faq(i)
            )
            self._faq_containers.append(item_container)

        self._faq_card = ft.Container(
            content=ft.Column(
                controls=[
                    self._faq_title,
                    ft.Column(controls=self._faq_containers, spacing=9)
                ],
                spacing=12
            ),
            bgcolor=card_bg,
            border=ft.Border.all(1, card_border),
            border_radius=12,
            padding=16
        )

        # ---------------------------------------------------------------------
        # 4. SOPORTE (Figma 72:5182)
        # ---------------------------------------------------------------------
        support_bg = "#141a2a" if self._tokens.mode == "dark" else "#f8fafc"
        support_border = "#1b2233" if self._tokens.mode == "dark" else "#e5e7eb"

        self._support_icon = ft.Icon(ft.Icons.QUESTION_ANSWER_ROUNDED, size=22, color="#a5b4ff" if self._tokens.mode == "dark" else "#5554d9")
        self._support_title = ft.Text(
            "¿Necesitas una mano?",
            size=13,
            weight=ft.FontWeight.W_600,
            color="#ffffff" if self._tokens.mode == "dark" else self._tokens.text_primary
        )
        self._support_desc = ft.Text(
            "Comparte tu registro con la comunidad en Discord.",
            size=11,
            color="#8f99b3" if self._tokens.mode == "dark" else "#6b7280"
        )

        self._discord_btn = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.NORTH_EAST_ROUNDED, size=14, color="#ffffff"),
                    ft.Text("Abrir Discord", size=12, color="#ffffff", weight=ft.FontWeight.NORMAL)
                ],
                spacing=8,
                alignment=ft.MainAxisAlignment.CENTER
            ),
            bgcolor=self._tokens.primary,
            border_radius=8,
            height=36,
            padding=ft.Padding.symmetric(horizontal=13),
            on_click=lambda _: self._open_discord(),
            ink=True
        )

        self._support_card = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Row(
                        controls=[
                            self._support_icon,
                            ft.Column(
                                controls=[self._support_title, self._support_desc],
                                spacing=5
                            )
                        ],
                        spacing=16,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        expand=True
                    ),
                    self._discord_btn
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER
            ),
            bgcolor=support_bg,
            border=ft.Border.all(1, support_border),
            border_radius=12,
            padding=16
        )

        # ---------------------------------------------------------------------
        # 5. FOOTER RECURSOS (Figma 72:5190)
        # ---------------------------------------------------------------------
        self._footer_guide_text = ft.Text(
            "AutoRod · Guía de la aplicación",
            size=10,
            color="#8f99b3" if self._tokens.mode == "dark" else "#9ca3af"
        )

        self._diag_link_text = ft.Text(
            "Copiar diagnóstico",
            size=11,
            color="#a5b4ff" if self._tokens.mode == "dark" else "#4f46e5"
        )
        self._copy_diag_btn = ft.Container(
            content=self._diag_link_text,
            on_click=lambda _: self._copy_diagnostics(),
            tooltip="Copiar información de diagnóstico al portapapeles"
        )

        self._release_link_text = ft.Text(
            "Ver novedades ↗",
            size=11,
            color="#a5b4ff" if self._tokens.mode == "dark" else "#4f46e5"
        )
        self._release_btn = ft.Container(
            content=self._release_link_text,
            on_click=lambda _: webbrowser.open("https://github.com/autorod/autorod/releases"),
            tooltip="Ver últimas notas de lanzamiento"
        )

        footer_row = ft.Row(
            controls=[
                self._footer_guide_text,
                ft.Row(
                    controls=[self._copy_diag_btn, self._release_btn],
                    spacing=20
                )
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER
        )

        # ---------------------------------------------------------------------
        # LAYOUT GENERAL (Figma 72:5140)
        # ---------------------------------------------------------------------
        content_column = ft.Column(
            controls=[
                presentation_header,
                self._search_bar_frame,
                self._steps_card,
                self._faq_card,
                self._support_card,
                footer_row
            ],
            spacing=16,
            scroll=ft.ScrollMode.ADAPTIVE
        )

        super().__init__(
            content=content_column,
            padding=ft.Padding.only(left=32, right=32, top=48, bottom=28),
            bgcolor=self._tokens.canvas_bg,
            border_radius=ft.BorderRadius.only(top_left=16, bottom_left=16),
            expand=True
        )

        self._theme_mgr.subscribe(self._on_theme_updated)

    def _toggle_faq(self, idx: int) -> None:
        self._faq_expanded_states[idx] = not self._faq_expanded_states[idx]
        is_open = self._faq_expanded_states[idx]
        self._faq_answer_texts[idx].visible = is_open
        self._faq_chevron_icons[idx].name = ft.Icons.KEYBOARD_ARROW_UP_ROUNDED if is_open else ft.Icons.KEYBOARD_ARROW_DOWN_ROUNDED
        safe_update(self._faq_containers[idx])

    def _open_discord(self) -> None:
        try:
            webbrowser.open("https://discord.gg/autorod")
        except Exception:
            pass

    def _copy_diagnostics(self) -> None:
        from autorod.infrastructure.updater.github_checker import CURRENT_VERSION
        diag = f"AutoRod v{CURRENT_VERSION} | OS: {platform.system()} {platform.release()} | Python: {platform.python_version()}"
        if self.page:
            try:
                self.page.set_clipboard(diag)
            except Exception:
                pass
        self._diag_link_text.value = "¡Diagnóstico copiado!"
        safe_update(self._diag_link_text)

    def _on_search_query(self, e: Any) -> None:
        q = (self._search_input.value or "").strip().lower()
        for idx, (question, answer) in enumerate(self._faq_data):
            matched = (q in question.lower()) or (q in answer.lower()) or (q == "")
            self._faq_containers[idx].visible = matched
        safe_update(self._faq_card)

    def _on_theme_updated(self, tokens: ThemeTokens) -> None:
        self.apply_theme(tokens)

    def apply_theme(self, tokens: ThemeTokens) -> None:
        self._tokens = tokens
        self.bgcolor = tokens.canvas_bg
        is_dark = tokens.mode == "dark"

        self._title_text.color = "#ffffff" if is_dark else tokens.text_primary
        self._subtitle_text.color = "#a5b4ff" if is_dark else tokens.text_secondary

        self._search_bar_frame.bgcolor = "#0d0f17" if is_dark else "#f9fafb"
        self._search_bar_frame.border = ft.Border.all(1, "#2a2f3a" if is_dark else "#e5e7eb")
        self._search_input.color = "#ffffff" if is_dark else tokens.text_primary

        card_bg = "#0d0f17" if is_dark else "#ffffff"
        card_border = "#1b2233" if is_dark else "#e5e7eb"

        self._steps_card.bgcolor = card_bg
        self._steps_card.border = ft.Border.all(1, card_border)
        self._steps_title.color = "#ffffff" if is_dark else tokens.text_primary

        self._faq_card.bgcolor = card_bg
        self._faq_card.border = ft.Border.all(1, card_border)
        self._faq_title.color = "#ffffff" if is_dark else tokens.text_primary

        support_bg = "#141a2a" if is_dark else "#f8fafc"
        support_border = "#1b2233" if is_dark else "#e5e7eb"
        self._support_card.bgcolor = support_bg
        self._support_card.border = ft.Border.all(1, support_border)
        self._support_title.color = "#ffffff" if is_dark else tokens.text_primary

        self._discord_btn.bgcolor = tokens.primary
        safe_update(self)
