import time
import logging
from collections.abc import Sequence
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
         inyecta un clic para jalar la caña. El minijuego se mantiene activo durante múltiples
         aciertos hasta que el pez es finalmente atrapado.
      3. CARD_DISMISS: Detecta y hace clic en la tarjeta de pez obtenido ('blank_card')
         para saltar la animación y reiniciar el ciclo hacia 'CAST!'.
    
    Garantía de Seguridad Industrial:
    La detección de la tarjeta ('blank_card') sólo emite clics cuando el bot
    se encuentra en fase post-minijuego (MINIGAME o CARD_DISMISS), descartando
    cualquier riesgo de falsos clics sobre áreas blancas del sistema operativo o navegador.
    """

    def __init__(
            self,
            click_cooldown_s: float = 0.35,
            state_machine: FishingStateMachine | None = None
    ) -> None:
        self.enabled = True
        self._last_click_time = 0.0
        self._cooldown_s = click_cooldown_s
        self._fsm = state_machine or FishingStateMachine(minigame_timeout_s=16.0, card_timeout_s=6.0)
        self._minigame_hits = 0

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

        # Si no hay objetivo confirmado, no accionar
        if not result.found:
            return []

        strategy = result.strategy_id

        # 2. FILTRO DE SEGURIDAD ESTRICTO:
        # Si se detecta una tarjeta blanca pero NO venimos del minijuego, IGNORAR por completo
        if strategy == "blank_card_detected" and self._fsm.state == FishingState.SCANNING:
            return []

        # 3. Control de debounce para evitar clics descontrolados
        if now - self._last_click_time < self._cooldown_s:
            return []

        commands: list[InputCommand] = []

        # 4. Transiciones y Lógica de Pesca Multi-Hit
        coords_str = f"({result.center.x}, {result.center.y})" if result.center else "(desconocido)"
        if strategy == "cast_button_detected":
            self._fsm.transition_to(FishingState.SCANNING, now)
            self._minigame_hits = 0
            logger.info("[BOTON] Botón 'CAST!' detectado y accionado en %s. Caña lanzada, esperando...", coords_str)

        elif strategy == "reel_button_detected":
            self._fsm.transition_to(FishingState.MINIGAME, now)
            self._minigame_hits = 0
            logger.info("[BOTON] ¡Pez picó el anzuelo! Botón 'REEL!' accionado en %s -> Iniciando MINIJUEGO.", coords_str)

        elif strategy == "minigame_needle_hit":
            # Si estábamos en SCANNING y apareció el minijuego, sincronizar FSM
            if self._fsm.state != FishingState.MINIGAME:
                self._fsm.transition_to(FishingState.MINIGAME, now)

            self._minigame_hits += 1
            logger.info(
                "[MINIJUEGO] ¡Zona verde alineada con aguja! Clic #%d inyectado en centro dial %s para jalar el pez.",
                self._minigame_hits, coords_str
            )
            # El estado se MANTIENE en MINIGAME porque el minijuego requiere múltiples aciertos
            self._fsm.state_entered_at = now

        elif strategy == "blank_card_detected":
            # El pez fue atrapado y se desplegó la tarjeta de recompensa
            logger.info(
                "[TARJETA] ¡Pez atrapado con éxito tras %d aciertos! Tarjeta de recompensa clickeada en %s para saltar animación. Retornando a SCANNING.",
                self._minigame_hits, coords_str
            )
            self._minigame_hits = 0
            self._fsm.transition_to(FishingState.SCANNING, now)

        # 5. Generación de comandos de ratón (Posicionamiento + Clic atómico)
        if result.center is not None:
            commands.append(
                MouseMove(x=result.center.x, y=result.center.y, absolute=True)
            )

        commands.append(MouseClick(button=MouseButton.LEFT, pressed=True))
        commands.append(MouseClick(button=MouseButton.LEFT, pressed=False))

        self._last_click_time = now
        return commands
