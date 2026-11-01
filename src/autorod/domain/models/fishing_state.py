from enum import Enum
from dataclasses import dataclass


class FishingState(Enum):
    """Estados del ciclo de automatización de pesca en lofi.town."""
    SCANNING = "SCANNING"              # Buscando botones CAST! y REEL!
    MINIGAME = "MINIGAME"              # Minijuego de aguja giratoria activo
    CARD_DISMISS = "CARD_DISMISS"      # Tarjeta blanca de pez atrapado lista para saltar


@dataclass
class FishingStateMachine:
    """
    Controlador de estados determinista para el ciclo de pesca.
    Asegura que la acción de cerrar la tarjeta (clic a rectángulo blanco)
    SÓLO se habilite tras haber interactuado exitosamente con el minijuego,
    eliminando cualquier riesgo de falsos clics en la interfaz del navegador.
    """
    state: FishingState = FishingState.SCANNING
    state_entered_at: float = 0.0
    minigame_timeout_s: float = 8.0
    card_timeout_s: float = 6.0

    def transition_to(self, new_state: FishingState, now: float) -> None:
        self.state = new_state
        self.state_entered_at = now

    def check_timeouts(self, now: float) -> bool:
        """
        Retorna True si hubo transición por timeout hacia SCANNING.
        Evita bloqueos en caso de que el usuario cierre el juego o falle la captura.
        """
        elapsed = now - self.state_entered_at
        if self.state == FishingState.MINIGAME and elapsed > self.minigame_timeout_s:
            self.transition_to(FishingState.SCANNING, now)
            return True
        elif self.state == FishingState.CARD_DISMISS and elapsed > self.card_timeout_s:
            self.transition_to(FishingState.SCANNING, now)
            return True
        return False
