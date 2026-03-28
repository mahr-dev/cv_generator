from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class Experience:
    empresa: str
    puesto: str
    anio_inicio: str
    anio_fin: str
    descripcion: str = ""


@dataclass(frozen=True)
class Education:
    institucion: str
    titulo: str
    anio_inicio: str
    anio_fin: str


@dataclass(frozen=True)
class Certification:
    nombre: str
    institucion: str = ""
    anio: str = ""


@dataclass(frozen=True)
class Contacto:
    email: str
    telefono: str = ""
    linkedin: str = ""
    website: str = ""
    ciudad: str = ""


@dataclass(frozen=True)
class DesignPreferences:
    """Preferencias de diseño del CV (capas de presentación).

    Todos los campos son opcionales: el generador PDF selecciona valores por
    defecto a partir del ``design_variant`` cuando no se especifican.
    """

    design_variant: int = 0          # índice del tema base (0-4)
    foto_position: str = "top-right" # "top-right" | "top-left" | "hidden"
    font_family: str = "helvetica"   # "helvetica" | "times"
    header_bg_color: Optional[str] = None  # "#RRGGBB" o None → usa el tema


@dataclass(frozen=True)
class CvData:
    nombre: str
    profesion: str
    breve_descripcion: Optional[str]
    foto_base64: Optional[str]
    experiencia_laboral: List[Experience]
    soft_skills: List[str]
    educacion: List[Education]
    hobbies: Optional[List[str]]
    certificaciones: Optional[List[Certification]]
    contacto: Contacto
    disponibilidad_laboral: str

