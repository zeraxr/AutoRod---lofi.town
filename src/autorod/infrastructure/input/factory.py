from autorod.domain.ports.input_simulator import IInputSimulator
from autorod.infrastructure.input.fake_input import FakeInputSimulator
from autorod.infrastructure.input.win32.sendinput import SendInputSimulator


class InputBackendFactory:
    @staticmethod
    def create(backend: str) -> IInputSimulator:
        if backend == "fake":
            return FakeInputSimulator()
        elif backend == "sendinput":
            return SendInputSimulator()
        elif backend == "interception":
            # Requiere importación perezosa
            from autorod.infrastructure.input.win32.interception import InterceptionInputSimulator
            return InterceptionInputSimulator()
        raise ValueError(f"Backend desconocido: {backend}")