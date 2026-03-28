"""Registro de fuentes para el generador PDF.

Al importar este módulo se intenta registrar fuentes TTF del sistema operativo
(Windows, Linux, macOS). Si un archivo de fuente no existe, esa familia se
omite y el generador recurrirá a las fuentes base de PDF (Helvetica / Times /
Courier), que siempre están disponibles sin archivos externos.

FONT_MAP  →  { font_key: (regular, bold, italic) }
FONT_META →  { font_key: { "display": str, "category": str } }
"""
from __future__ import annotations

import logging
import os
from typing import Optional

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

logger = logging.getLogger(__name__)

# ── Directorios de búsqueda (en orden de prioridad) ──────────────────────────
_FONT_DIRS: list[str] = [
    r"C:\Windows\Fonts",          # Windows 10/11
    "/usr/share/fonts/truetype",  # Ubuntu/Debian
    "/usr/share/fonts",           # Linux general
    "/System/Library/Fonts",      # macOS
    "/Library/Fonts",             # macOS usuario
]

# ── Candidatos TTF: (key, display_name, [(reg_name, file_basename), ...]) ────
# El orden de la lista es (regular, bold, italic). Si falta algún archivo
# la familia entera se descarta.
_TTF_CANDIDATES: list[tuple[str, str, str, list[tuple[str, str]]]] = [
    # key         display                      category   regular/bold/italic
    ("arial",    "Profesional · Arial",        "sans",    [
        ("Arial",        "arial.ttf"),
        ("Arial-Bold",   "arialbd.ttf"),
        ("Arial-Italic", "ariali.ttf"),
    ]),
    ("calibri",  "Moderna · Calibri",          "sans",    [
        ("Calibri",        "calibri.ttf"),
        ("Calibri-Bold",   "calibrib.ttf"),
        ("Calibri-Italic", "calibrii.ttf"),
    ]),
    ("georgia",  "Elegante · Georgia",         "serif",   [
        ("Georgia",        "georgia.ttf"),
        ("Georgia-Bold",   "georgiab.ttf"),
        ("Georgia-Italic", "georgiai.ttf"),
    ]),
    ("verdana",  "Legible · Verdana",          "sans",    [
        ("Verdana",        "verdana.ttf"),
        ("Verdana-Bold",   "verdanab.ttf"),
        ("Verdana-Italic", "verdanai.ttf"),
    ]),
    ("trebuchet","Compacta · Trebuchet MS",    "sans",    [
        ("Trebuchet",        "trebuc.ttf"),
        ("Trebuchet-Bold",   "trebucbd.ttf"),
        ("Trebuchet-Italic", "trebucit.ttf"),
    ]),
    ("garamond", "Clásica · Garamond",         "serif",   [
        ("Garamond",        "GARA.TTF"),
        ("Garamond-Bold",   "GARABD.TTF"),
        ("Garamond-Italic", "GARAit.TTF"),
    ]),
]

# ── Fuentes base PDF (siempre disponibles, sin archivos) ─────────────────────
_BUILTIN: dict[str, tuple[str, str, str]] = {
    "helvetica": ("Helvetica",   "Helvetica-Bold",   "Helvetica-Oblique"),
    "times":     ("Times-Roman", "Times-Bold",       "Times-Italic"),
    "courier":   ("Courier",     "Courier-Bold",     "Courier-Oblique"),
}

_BUILTIN_META: dict[str, dict[str, str]] = {
    "helvetica": {"display": "Sans · Helvetica",    "category": "sans"},
    "times":     {"display": "Serif · Times Roman", "category": "serif"},
    "courier":   {"display": "Técnica · Courier",   "category": "mono"},
}

# ── Registro público (exportado) ──────────────────────────────────────────────
FONT_MAP:  dict[str, tuple[str, str, str]] = dict(_BUILTIN)   # key → (reg, bold, italic)
FONT_META: dict[str, dict[str, str]]       = dict(_BUILTIN_META)


def _find_font_file(filename: str) -> Optional[str]:
    """Busca ``filename`` en los directorios conocidos; devuelve la ruta o None."""
    for directory in _FONT_DIRS:
        path = os.path.join(directory, filename)
        if os.path.isfile(path):
            return path
    return None


def _register_family(
    key: str,
    display: str,
    category: str,
    variants: list[tuple[str, str]],
) -> bool:
    """Registra una familia TTF. Devuelve True si tuvo éxito, False si falta algún archivo."""
    resolved: list[tuple[str, str]] = []
    for name, filename in variants:
        path = _find_font_file(filename)
        if path is None:
            logger.debug("Fuente no encontrada: %s (%s) — familia '%s' omitida.", filename, name, key)
            return False
        resolved.append((name, path))

    # Todos los archivos encontrados: registrar
    try:
        for name, path in resolved:
            pdfmetrics.registerFont(TTFont(name, path))
        FONT_MAP[key]  = (resolved[0][0], resolved[1][0], resolved[2][0])
        FONT_META[key] = {"display": display, "category": category}
        logger.debug("Familia registrada: %s → %s", key, [r[0] for r in resolved])
        return True
    except Exception as exc:
        logger.warning("Error al registrar fuente '%s': %s", key, exc)
        return False


# ── Inicialización (se ejecuta una vez al importar) ───────────────────────────
for _key, _display, _category, _variants in _TTF_CANDIDATES:
    _register_family(_key, _display, _category, _variants)

logger.debug("Fuentes disponibles: %s", list(FONT_MAP.keys()))
