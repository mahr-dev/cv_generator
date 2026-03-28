from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Optional  # noqa: F401 — usado en _to_domain_prefs

from fastapi import APIRouter, Request
from fastapi.responses import Response

from cvgen.adapters.http.dependencies import build_generate_cv_use_case
from cvgen.adapters.http.schemas import GenerateCvRequest
from cvgen.domain.model import Certification, Contacto, CvData, DesignPreferences, Education, Experience

router = APIRouter(prefix="/api/cv", tags=["cv"])


def _sanitize_filename(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")
    return value or "cv"


def _to_domain_cv(dto: GenerateCvRequest) -> CvData:
    cv = dto.cv
    return CvData(
        nombre=cv.nombre,
        profesion=cv.profesion,
        breve_descripcion=cv.breve_descripcion,
        foto_base64=cv.foto_base64,
        experiencia_laboral=[
            Experience(
                empresa=e.empresa,
                puesto=e.puesto,
                anio_inicio=e.anio_inicio,
                anio_fin=e.anio_fin,
                descripcion=e.descripcion or "",
            )
            for e in (cv.experiencia_laboral or [])
        ],
        soft_skills=[s for s in (cv.soft_skills or []) if s],
        educacion=[
            Education(
                institucion=e.institucion,
                titulo=e.titulo,
                anio_inicio=e.anio_inicio,
                anio_fin=e.anio_fin,
            )
            for e in (cv.educacion or [])
        ],
        hobbies=cv.hobbies if cv.hobbies else None,
        certificaciones=[
            Certification(nombre=c.nombre, institucion=c.institucion or "", anio=c.anio or "")
            for c in (cv.certificaciones or [])
        ]
        if cv.certificaciones
        else None,
        contacto=Contacto(
            email=cv.contacto.email,
            telefono=cv.contacto.telefono or "",
            linkedin=cv.contacto.linkedin or "",
            website=cv.contacto.website or "",
            ciudad=cv.contacto.ciudad or "",
        ),
        disponibilidad_laboral=cv.disponibilidad_laboral,
    )


USE_CASE = build_generate_cv_use_case()


def _to_domain_prefs(req: GenerateCvRequest) -> Optional[DesignPreferences]:
    """Convierte el DTO de preferencias al modelo de dominio."""
    if req.design_preferences is None:
        return None
    dp = req.design_preferences
    return DesignPreferences(
        design_variant=dp.design_variant,
        foto_position=dp.foto_position,
        font_family=dp.font_family,
        header_bg_color=dp.header_bg_color or None,
    )


@router.post("/generate")
def generate_cv(req: GenerateCvRequest, http_request: Request) -> Response:
    domain_cv    = _to_domain_cv(req)
    domain_prefs = _to_domain_prefs(req)

    ip         = http_request.client.host if http_request.client else "unknown"
    user_agent = http_request.headers.get("user-agent") or ""
    log_usage  = http_request.headers.get("x-cv-preview") != "1"

    content = USE_CASE.execute(
        cv=domain_cv,
        output_format=req.output_format,
        font_color=req.font_color,
        design_preferences=domain_prefs,
        ip=ip,
        user_agent=user_agent,
        payload=req.model_dump(),
        log_usage=log_usage,
    )

    ext = req.output_format.lower().strip()
    content_type = "application/pdf" if ext == "pdf" else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"cv_{_sanitize_filename(req.cv.nombre)}_{ts}.{ext}"

    return Response(
        content=content,
        media_type=content_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

