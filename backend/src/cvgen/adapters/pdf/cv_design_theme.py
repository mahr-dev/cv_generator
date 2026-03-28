"""Definición de temas visuales para el CV en PDF.

Cada ``CvTheme`` describe las características de presentación de un diseño
formal. Los cinco temas predefinidos son completamente profesionales y varían
de forma sutil en tipografía, color de cabecera y posición de la fotografía.

El generador PDF importa ``THEMES`` y selecciona el índice correspondiente
al ``DesignPreferences.design_variant`` recibido en la solicitud.

``FONT_MAP`` se re-exporta desde ``font_registry`` para que el generador PDF
solo tenga que importar desde este módulo.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

# Registro de fuentes: incluye built-ins (Helvetica/Times/Courier) +
# fuentes TTF del sistema si están disponibles (Arial, Calibri, etc.)
from cvgen.adapters.pdf.font_registry import FONT_MAP  # noqa: F401 — re-exportado


@dataclass(frozen=True)
class CvTheme:
    """Parámetros visuales base de un diseño de CV.

    Attributes:
        name: Nombre descriptivo (solo informativo).
        font_key: Clave de familia tipográfica; debe existir en ``FONT_MAP``.
        header_bg: Color de fondo del encabezado en RGB 0-1.
        photo_position: Posición por defecto de la fotografía ("top-right"|"top-left").
        name_size: Tamaño de fuente para el nombre del candidato.
    """

    name: str
    font_key: str
    header_bg: Tuple[float, float, float]
    photo_position: str
    name_size: int


# ---------------------------------------------------------------------------
# Temas predefinidos (todos formales)
# Los font_key que no estén en FONT_MAP en tiempo de ejecución se degradan
# automáticamente a "helvetica" dentro del generador PDF.
# ---------------------------------------------------------------------------

THEMES: list[CvTheme] = [
    # 0 — Clásico
    CvTheme(
        name="Clásico",
        font_key="helvetica",
        header_bg=(0.93, 0.93, 0.93),   # gris neutro
        photo_position="top-right",
        name_size=22,
    ),
    # 1 — Ejecutivo
    CvTheme(
        name="Ejecutivo",
        font_key="times",
        header_bg=(0.90, 0.93, 0.97),   # azul-gris suave
        photo_position="top-right",
        name_size=22,
    ),
    # 2 — Moderno
    CvTheme(
        name="Moderno",
        font_key="calibri",
        header_bg=(0.95, 0.93, 0.88),   # crema cálido
        photo_position="top-left",
        name_size=24,
    ),
    # 3 — Corporativo
    CvTheme(
        name="Corporativo",
        font_key="georgia",
        header_bg=(0.91, 0.95, 0.91),   # verde salvia
        photo_position="top-right",
        name_size=20,
    ),
    # 4 — Elegante
    CvTheme(
        name="Elegante",
        font_key="arial",
        header_bg=(0.95, 0.93, 0.97),   # lavanda suave
        photo_position="top-left",
        name_size=22,
    ),
]
