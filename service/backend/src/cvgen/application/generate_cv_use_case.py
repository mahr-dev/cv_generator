from __future__ import annotations

import logging
from typing import Dict, Optional

from cvgen.application.description_generator import DescriptionGenerator
from cvgen.domain.model import CvData, DesignPreferences
from cvgen.domain.ports.cv_document_generator import CvDocumentGenerator
from cvgen.domain.ports.usage_repository import UsageRepository

logger = logging.getLogger(__name__)


class GenerateCvUseCase:
    def __init__(
        self,
        *,
        usage_repository: UsageRepository,
        document_generators: Dict[str, CvDocumentGenerator],
        description_generator: Optional[DescriptionGenerator] = None,
    ) -> None:
        self._usage_repository = usage_repository
        self._document_generators = document_generators
        self._description_generator = description_generator or DescriptionGenerator()

    def execute(
        self,
        *,
        cv: CvData,
        output_format: str,
        font_color: Optional[str],
        design_preferences: Optional[DesignPreferences] = None,
        ip: str,
        user_agent: str,
        payload: Dict,
        log_usage: bool = True,
    ) -> bytes:
        normalized_format = output_format.lower().strip()
        if normalized_format not in self._document_generators:
            raise ValueError(f"Formato no soportado: {output_format}")

        breve = cv.breve_descripcion
        if not breve or not breve.strip():
            breve = self._description_generator.generate(cv)
            cv = CvData(
                nombre=cv.nombre,
                profesion=cv.profesion,
                breve_descripcion=breve,
                foto_base64=cv.foto_base64,
                experiencia_laboral=cv.experiencia_laboral,
                soft_skills=cv.soft_skills,
                educacion=cv.educacion,
                hobbies=cv.hobbies,
                certificaciones=cv.certificaciones,
                contacto=cv.contacto,
                disponibilidad_laboral=cv.disponibilidad_laboral,
            )

        generator = self._document_generators[normalized_format]
        content = generator.generate(cv, font_color=font_color, design_preferences=design_preferences)

        if log_usage:
            # Best-effort logging: nunca debe romper la generación del CV.
            try:
                self._usage_repository.log_usage(
                    ip=ip,
                    user_agent=user_agent,
                    output_format=normalized_format,
                    font_color=font_color,
                    payload=payload,
                )
            except Exception:
                logger.exception("Error registrando uso en Mongo (best-effort).")

        return content

