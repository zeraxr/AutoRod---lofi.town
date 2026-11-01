from autorod.domain.models.input_commands import KeyCode

# Mapeo puro agnóstico a Virtual-Key / Scan Codes de Ring 0.
KEY_TO_SCANCODE: dict[KeyCode, int] = {
    KeyCode.SPACE: 0x39,
    KeyCode.ENTER: 0x1C,
    KeyCode.Q: 0x10,
}