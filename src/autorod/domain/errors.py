class AutoRodError(Exception):
    """Clase base para excepciones del dominio."""

class VisionError(AutoRodError):
    """Error crítico durante el análisis del motor matemático."""

class CaptureError(AutoRodError):
    """Error al intentar leer de la fuente de fotogramas."""

class InputBackendUnavailableError(AutoRodError):
    """Lanzada cuando un driver o librería de nivel OS no está disponible."""

class ComponentClosedError(AutoRodError):
    """Lanzada si se interactúa con un puerto previamente cerrado."""

class TemplateNotFoundError(AutoRodError):
    """Lanzada cuando un recurso de plantilla visual no existe en el repositorio."""
