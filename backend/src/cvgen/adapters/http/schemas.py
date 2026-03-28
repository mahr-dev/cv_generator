from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class ExperienceDTO(BaseModel):
    empresa: str = ""
    puesto: str = ""
    anio_inicio: str = ""
    anio_fin: str = ""
    descripcion: str = ""


class EducationDTO(BaseModel):
    institucion: str = ""
    titulo: str = ""
    anio_inicio: str = ""
    anio_fin: str = ""


class CertificationDTO(BaseModel):
    nombre: str = ""
    institucion: str = ""
    anio: str = ""


class ContactoDTO(BaseModel):
    email: str = ""
    telefono: str = ""
    linkedin: str = ""
    website: str = ""
    ciudad: str = ""


class CvDTO(BaseModel):
    nombre: str = ""
    profesion: str = ""
    breve_descripcion: Optional[str] = None
    # Base64 sin prefijo data: (ej: "iVBORw0KGgo...")
    foto_base64: Optional[str] = None
    experiencia_laboral: List[ExperienceDTO] = []
    soft_skills: List[str] = []
    educacion: List[EducationDTO] = []
    hobbies: Optional[List[str]] = None
    certificaciones: Optional[List[CertificationDTO]] = None
    contacto: ContactoDTO = ContactoDTO()
    disponibilidad_laboral: str = ""


class DesignPreferencesDTO(BaseModel):
    """Preferencias visuales del CV enviadas por el frontend."""

    design_variant: int = Field(default=0, ge=0)
    foto_position: Literal["top-right", "top-left", "hidden"] = "top-right"
    font_family: str = "helvetica"
    header_bg_color: Optional[str] = None


class GenerateCvRequest(BaseModel):
    cv: CvDTO = CvDTO()
    output_format: Literal["pdf", "docx"] = "pdf"
    font_color: Optional[str] = "#111111"
    design_preferences: Optional[DesignPreferencesDTO] = None
