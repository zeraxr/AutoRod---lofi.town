"""DEPRECATED: Módulo Tkinter original de AutoRod.

ADVERTENCIA PARA AGENTES Y DESARROLLADORES:
------------------------------------------
Este módulo ha sido completamente DEPRECADO y REEMPLAZADO por la arquitectura
moderna basada en Flet (Flutter) ubicada en:
    `autorod.infrastructure.ui.flet`

NO REFERENCIAR ni importar componentes de Tkinter (Frame, Canvas, Toplevel, etc.).
Todos los controles, vistas y botones ahora residen en:
    `autorod.infrastructure.ui.flet.components`
"""

import warnings

warnings.warn(
    "El paquete 'autorod.infrastructure.ui.tk' está deprecado. "
    "Utilice 'autorod.infrastructure.ui.flet' en su lugar.",
    DeprecationWarning,
    stacklevel=2,
)
