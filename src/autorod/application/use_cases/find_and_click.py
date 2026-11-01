import time
import logging
from collections.abc import Sequence
from autorod.domain.models.geometry import Point
from autorod.domain.models.input_commands import (
    InputCommand,
    MouseClick,
    MouseButton,
    MouseMove,
)
from autorod.domain.models.match_result import MatchResult
from autorod.domain.models.fishing_state import FishingState, FishingStateMachine
from autorod.domain.ports.actions import IBotTask

logger = logging.getLogger(__name__)


class FindAndClickTask(IBotTask):
    """
    Caso de uso de interacción autónoma para pesca continua en lofi.town.
    Orquestado mediante una máquina de estados determinista (FSM):
      1. SCANNING: Busca y acciona botones 'CAST!' y 'REEL!'.
      2. MINIGAME (Multi-Hit): Cada vez que la zona verde gira bajo la aguja fija superior,
         inyecta un clic ultra-rápido para jalar la caña. El minijuego se mantiene activo durante múltiples
         aciertos hasta que el pez es finalmente atrapado.
      3. CARD_DISMISS (Ráfaga acotada y segura): Al desplegarse la tarjeta de recompensa post-minijuego,
         emite una ráfaga precisa de hasta 3 clics (a 350 ms de cadencia y 50 ms de pulsación física)
         durante un máximo de 1.2 segundos para revelar el pez y cerrar el diálogo.
         Al completar el tercer clic (o si reaparece CAST!), finaliza de inmediato la secuencia y retorna
         a SCANNING para evitar clics ciegos sobre avatares de otros jugadores en el mapa.
    
    Garantía de Seguridad Industrial:
    La detección de la tarjeta ('blank_card') sólo emite clics cuando el bot
    se encuentra en fase post-minijuego (MINIGAME o CARD_DISMISS), descartando
    cualquier riesgo de falsos clics sobre áreas blancas del sistema operativo o navegador.
    """

    def __init__(
            self,
            click_cooldown_s: float = 0.35,
            minigame_cooldown_s: float = 0.22,
            card_dismiss_duration_s: float = 1.60,
            card_initial_delay_s: float = 0.50,
            card_cooldown_s: float = 0.12,
            max_card_dismiss_clicks: int = 5,
            state_machine: FishingStateMachine | None = None
    ) -> None:
        self.enabled = True
        self._last_click_time = 0.0
        self._cooldown_s = click_cooldown_s
        self._minigame_cooldown_s = minigame_cooldown_s
        self._card_dismiss_duration_s = card_dismiss_duration_s
        self._card_initial_delay_s = card_initial_delay_s
        self._card_cooldown_s = card_cooldown_s
        self._max_card_dismiss_clicks = max_card_dismiss_clicks
        self._fsm = state_machine or FishingStateMachine(minigame_timeout_s=16.0, card_timeout_s=6.0)
        self._minigame_hits = 0
        self._card_dismiss_clicks = 0
        self._card_dismiss_start = 0.0
        self._last_card_center: Point | None = None

    @property
    def state_machine(self) -> FishingStateMachine:
        return self._fsm

    @property
    def current_state(self) -> FishingState:
        return self._fsm.state

    def evaluate(self, result: MatchResult) -> Sequence[InputCommand]:
        if not self.enabled:
            return []

        now = time.monotonic()

        # 1. Verificar y resolver timeouts de seguridad hacia SCANNING
        if self._fsm.check_timeouts(now):
            logger.warning("[FSM] Timeout de inactividad alcanzado. Restableciendo ciclo a SCANNING.")
            self._minigame_hits = 0
            self._card_dismiss_clicks = 0
            self._last_card_center = None

        strategy = result.strategy_id

        # 2. MANEJO DE DESCARTE DE TARJETA (CARD_DISMISS - Secuencia v1.1.0 restaurada):
        # Fase 1 (0.0s - 0.5s): Espera de 500 ms para que termine la animación de entrada de la tarjeta.
        # Fase 2 (0.5s - 1.1s): Ráfaga exacta de 5 clics firmes con cadencia de 120 ms (spam_click(5)).
        # Fase 3 (1.1s - 1.6s): Espera de 500 ms con clics detenidos al 100% para que la tarjeta se cierre.
        # Retorno inmediato a SCANNING si reaparece 'CAST!' en cualquier momento.
        if self._fsm.state == FishingState.CARD_DISMISS:
            # Si el botón 'CAST!' ya reapareció, la tarjeta fue superada exitosamente y podemos lanzar de inmediato
            if strategy == "cast_button_detected" and result.found:
                logger.info("[TARJETA] Botón 'CAST!' detectado. Tarjeta cerrada exitosamente. Retornando a SCANNING.")
                self._fsm.transition_to(FishingState.SCANNING, now)
                self._card_dismiss_clicks = 0
                self._minigame_hits = 0
                self._last_card_center = None
                # Se procesará como botón CAST! abajo
            else:
                elapsed = now - self._card_dismiss_start

                # Fin del ciclo total (1.6s): retornar a SCANNING
                if elapsed >= self._card_dismiss_duration_s:
                    logger.info(
                        "[TARJETA] Descarte de tarjeta v1.1.0 completado con éxito tras %d clics (%.2fs). Retornando a SCANNING.",
                        self._card_dismiss_clicks, elapsed
                    )
                    self._fsm.transition_to(FishingState.SCANNING, now)
                    self._card_dismiss_clicks = 0
                    self._minigame_hits = 0
                    self._last_card_center = None
                    return []

                # Si la tarjeta sigue detectada, refrescar su centro
                if strategy == "blank_card_detected" and result.center is not None:
                    self._last_card_center = result.center

                # Fase 1: Espera inicial de asentamiento (0.0s - 0.50s)
                if elapsed < self._card_initial_delay_s:
                    return []

                # Fase 2: Ráfaga firme de hasta 5 clics a 120 ms de cadencia
                if self._card_dismiss_clicks < self._max_card_dismiss_clicks:
                    if now - self._last_click_time >= self._card_cooldown_s:
                        target_pt = self._last_card_center or result.center
                        if target_pt is not None:
                            self._card_dismiss_clicks += 1
                            self._last_click_time = now
                            self._fsm.state_entered_at = now
                            logger.info(
                                "[TARJETA] Clic v1.1.0 #%d/%d inyectado en (%d, %d)...",
                                self._card_dismiss_clicks, self._max_card_dismiss_clicks, target_pt.x, target_pt.y
                            )
                            return [
                                MouseMove(x=target_pt.x, y=target_pt.y, absolute=True),
                                MouseClick(button=MouseButton.LEFT, pressed=True),
                                MouseClick(button=MouseButton.LEFT, pressed=False),
                            ]
                    return []

                # Fase 3: Los 5 clics fueron emitidos. Clics totalmente detenidos hasta expirar el tiempo de salida.
                return []

        # Si no hay objetivo confirmado y no estamos en CARD_DISMISS, no accionar
        if not result.found:
            return []

        # 3. FILTRO DE SEGURIDAD ESTRICTO:
        # Si se detecta una tarjeta blanca pero NO venimos del minijuego, IGNORAR por completo
        if strategy == "blank_card_detected" and self._fsm.state == FishingState.SCANNING:
            return []

        # 4. Control de cooldown adaptativo según el contexto operativo
        effective_cooldown = self._cooldown_s
        if strategy == "minigame_needle_hit":
            effective_cooldown = self._minigame_cooldown_s
        elif strategy == "blank_card_detected":
            effective_cooldown = self._card_cooldown_s

        if now - self._last_click_time < effective_cooldown:
            return []

        commands: list[InputCommand] = []

        # 5. Transiciones y Lógica de Pesca Multi-Hit
        coords_str = f"({result.center.x}, {result.center.y})" if result.center else "(desconocido)"
        if strategy == "cast_button_detected":
            self._fsm.transition_to(FishingState.SCANNING, now)
            self._minigame_hits = 0
            self._card_dismiss_clicks = 0
            self._last_card_center = None
            logger.info("[BOTON] Botón 'CAST!' detectado y accionado en %s. Caña lanzada, esperando...", coords_str)

        elif strategy == "reel_button_detected":
            self._fsm.transition_to(FishingState.MINIGAME, now)
            self._minigame_hits = 0
            self._card_dismiss_clicks = 0
            self._last_card_center = None
            logger.info("[BOTON] ¡Pez picó el anzuelo! Botón 'REEL!' accionado en %s -> Iniciando MINIJUEGO.", coords_str)

        elif strategy == "minigame_needle_hit":
            if self._fsm.state != FishingState.MINIGAME:
                self._fsm.transition_to(FishingState.MINIGAME, now)

            self._minigame_hits += 1
            logger.info(
                "[MINIJUEGO] ¡Zona verde alineada con aguja! Clic #%d inyectado en centro dial %s para jalar el pez.",
                self._minigame_hits, coords_str
            )
            self._fsm.state_entered_at = now

        elif strategy == "blank_card_detected":
            # El pez fue atrapado y se desplegó la tarjeta de recompensa por primera vez.
            # En v1.1.0: se esperan 0.5s de animación inicial antes de emitir ningún clic.
            self._fsm.transition_to(FishingState.CARD_DISMISS, now)
            self._card_dismiss_start = now
            self._card_dismiss_clicks = 0
            self._last_card_center = result.center
            self._last_click_time = 0.0
            logger.info(
                "[TARJETA] ¡Pez atrapado tras %d aciertos en minijuego! Tarjeta detectada en %s -> "
                "Iniciando secuencia v1.1.0 (Espera 0.5s -> 5 clics firmes -> Espera salida)...",
                self._minigame_hits, coords_str
            )
            # Fase 1: Asentamiento de entrada (no cliquear en el primer fotograma)
            return []

        # 6. Generación de comandos de ratón (Posicionamiento + Clic atómico)
        if result.center is not None:
            commands.append(
                MouseMove(x=result.center.x, y=result.center.y, absolute=True)
            )

        commands.append(MouseClick(button=MouseButton.LEFT, pressed=True))
        commands.append(MouseClick(button=MouseButton.LEFT, pressed=False))

        self._last_click_time = now
        return commands
