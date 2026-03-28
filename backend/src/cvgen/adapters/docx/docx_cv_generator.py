from __future__ import annotations

import base64
import io
from typing import Optional

from docx import Document
from docx.shared import Pt, RGBColor

from cvgen.adapters.document_utils import parse_hex_color_int
from cvgen.domain.model import CvData, DesignPreferences
from cvgen.domain.ports.cv_document_generator import CvDocumentGenerator


class DocxCvGenerator(CvDocumentGenerator):
    def content_type(self) -> str:
        return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

    def file_extension(self) -> str:
        return "docx"

    def _set_paragraph_color(self, paragraph, rgb: RGBColor) -> None:
        for run in paragraph.runs:
            run.font.color.rgb = rgb

    def generate(
        self,
        cv: CvData,
        *,
        font_color: Optional[str],
        design_preferences: Optional[DesignPreferences] = None,
    ) -> bytes:
        # design_preferences se ignora en DOCX por ahora (reservado para futuras versiones).
        doc = Document()
        r, g, b = parse_hex_color_int(font_color)
        rgb = RGBColor(r, g, b)

        def add_divider() -> None:
            # Separador visual simple (linea larga).
            p = doc.add_paragraph()
            run = p.add_run("_" * 55)
            run.font.size = Pt(7)
            run.font.color.rgb = rgb

        def add_section_title(title: str) -> None:
            p = doc.add_paragraph()
            run = p.add_run(title.upper())
            run.bold = True
            run.font.size = Pt(12)
            run.font.color.rgb = rgb
            add_divider()

        # Estilo minimal: nombre + profesion + secciones.
        title = doc.add_paragraph()
        run = title.add_run(cv.nombre)
        run.bold = True
        run.font.size = Pt(20)
        run.font.color.rgb = rgb

        # Foto (si viene)
        if cv.foto_base64:
            try:
                img_bytes = base64.b64decode(cv.foto_base64)
                bio = io.BytesIO(img_bytes)
                doc.add_picture(bio, width=Pt(110))
            except Exception:
                pass

        prof = doc.add_paragraph()
        prof_run = prof.add_run(cv.profesion)
        prof_run.bold = True
        prof_run.font.size = Pt(12)
        self._set_paragraph_color(prof, rgb)

        if cv.breve_descripcion:
            p = doc.add_paragraph()
            run2 = p.add_run(cv.breve_descripcion)
            run2.font.size = Pt(11)
            self._set_paragraph_color(p, rgb)
            add_divider()

        if cv.experiencia_laboral:
            add_section_title("EXPERIENCIA")
            for e in cv.experiencia_laboral:
                p = doc.add_paragraph()
                r1 = p.add_run(f"{e.puesto} - {e.empresa} ({e.anio_inicio} - {e.anio_fin})")
                r1.bold = True
                r1.font.size = Pt(11)
                self._set_paragraph_color(p, rgb)

                if e.descripcion:
                    d = doc.add_paragraph()
                    r2 = d.add_run(e.descripcion)
                    r2.font.size = Pt(10.5)
                    self._set_paragraph_color(d, rgb)

                doc.add_paragraph()

        if cv.soft_skills:
            add_section_title("SOFT SKILLS")
            for s in [x for x in cv.soft_skills if x]:
                p = doc.add_paragraph()
                r1 = p.add_run(f"• {s}")
                r1.font.size = Pt(11)
                self._set_paragraph_color(p, rgb)
            doc.add_paragraph()

        if cv.educacion:
            add_section_title("EDUCACIÓN")
            for edu in cv.educacion:
                p = doc.add_paragraph()
                r1 = p.add_run(f"{edu.titulo} - {edu.institucion} ({edu.anio_inicio} - {edu.anio_fin})")
                r1.bold = True
                r1.font.size = Pt(11)
                self._set_paragraph_color(p, rgb)
            doc.add_paragraph()

        if cv.hobbies:
            hobbies = [x for x in cv.hobbies if x]
            if hobbies:
                add_section_title("HOBBIES")
                p = doc.add_paragraph()
                p.add_run(", ".join(hobbies)).font.size = Pt(11)
                self._set_paragraph_color(p, rgb)
                doc.add_paragraph()

        if cv.certificaciones:
            add_section_title("CERTIFICACIONES")
            for c in cv.certificaciones:
                p = doc.add_paragraph()
                label = c.nombre
                if c.institucion:
                    label += f" - {c.institucion}"
                if c.anio:
                    label += f" ({c.anio})"
                r1 = p.add_run(label)
                r1.font.size = Pt(11)
                self._set_paragraph_color(p, rgb)
            doc.add_paragraph()

        # Contacto y disponibilidad al final.
        add_section_title("CONTACTO")
        p = doc.add_paragraph()
        parts = [cv.contacto.email]
        if cv.contacto.telefono:
            parts.append(cv.contacto.telefono)
        if cv.contacto.linkedin:
            parts.append(cv.contacto.linkedin)
        if cv.contacto.website:
            parts.append(cv.contacto.website)
        if cv.contacto.ciudad:
            parts.append(cv.contacto.ciudad)
        p.add_run(" | ".join(parts)).font.size = Pt(11)
        self._set_paragraph_color(p, rgb)
        add_section_title("DISPONIBILIDAD LABORAL")
        p2 = doc.add_paragraph()
        p2.add_run(cv.disponibilidad_laboral).font.size = Pt(11)
        self._set_paragraph_color(p2, rgb)

        buf = io.BytesIO()
        doc.save(buf)
        return buf.getvalue()

