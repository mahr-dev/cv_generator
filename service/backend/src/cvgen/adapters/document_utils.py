from __future__ import annotations

from typing import Optional, Tuple


def parse_hex_color(font_color: Optional[str]) -> Tuple[float, float, float]:
    """
    Convierte '#RRGGBB' en floats entre 0 y 1 para PDF/estilos.
    """
    default = (17 / 255, 17 / 255, 17 / 255)  # '#111111'
    if not font_color:
        return default

    value = font_color.strip()
    if value.startswith("#"):
        value = value[1:]

    if len(value) != 6:
        return default

    try:
        r = int(value[0:2], 16) / 255.0
        g = int(value[2:4], 16) / 255.0
        b = int(value[4:6], 16) / 255.0
    except ValueError:
        return default

    return (r, g, b)


def parse_hex_color_int(font_color: Optional[str]) -> Tuple[int, int, int]:
    if not font_color:
        return (17, 17, 17)
    value = font_color.strip()
    if value.startswith("#"):
        value = value[1:]
    if len(value) != 6:
        return (17, 17, 17)
    try:
        r = int(value[0:2], 16)
        g = int(value[2:4], 16)
        b = int(value[4:6], 16)
    except ValueError:
        return (17, 17, 17)
    return (r, g, b)

