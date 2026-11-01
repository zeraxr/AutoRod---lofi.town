from autorod.domain.ports.input_simulator import IInputSimulator
from autorod.infrastructure.input.fake_input import FakeInputSimulator
from autorod.infrastructure.input.win32.sendinput import SendInputSimulator


class InputBackendFactory:
    @staticmethod
    def create(backend: str) -> IInputSimulator:
        backend_clean = backend.strip().lower()
        if backend_clean in ("fake", "mock"):
            return FakeInputSimulator()
        elif backend_clean in ("sendinput", "legacy"):
            return SendInputSimulator()
        elif backend_clean in ("postmessage", "nuevo", "background"):
            from autorod.infrastructure.input.win32.postmessage import Win32PostMessageSimulator
            return Win32PostMessageSimulator()
        elif backend_clean in ("interception", "driver", "kernel"):
            # Requiere importación perezosa
            from autorod.infrastructure.input.win32.interception import InterceptionInputSimulator
            return InterceptionInputSimulator()
        raise ValueError(f"Backend desconocido: {backend}")
