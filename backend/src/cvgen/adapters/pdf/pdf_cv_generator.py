"""Generador de CV en formato PDF usando ReportLab.

Arquitectura del layout (A4, sistema de coordenadas ReportLab: y=0 es abajo):

    ┌──────────────────────────────────────────────────────────────┐  hdr_top
    │  CABECERA  (fondo gris/color tema)                           │
    │  [Foto con marco]   Nombre · Profesión · Descripción breve   │
    └──────────────────────────────────────────────────────────────┘  hdr_bot
    ──────────────── línea divisora acento ──────────────────────────  div_y
    │ COLUMNA IZQ (33%) │              COLUMNA DER (67%)           │
    │ Contacto          │  Experiencia                             │
    │ Habilidades       │  Educación                               │
    │ Intereses         │  Certificaciones                         │
    │                   │                                          │
    ──────────────── línea divisora acento ──────────────────────────  footer_line_y
    │ DISPONIBILIDAD LABORAL: valor                                │
    └──────────────────────────────────────────────────────────────┘  MB

Las líneas divisoras se dibujan *fuera* de las zonas de texto, con margen
mínimo de 5-6 pt bajo la línea base de la fuente, garantizando que nunca
se superpongan sobre letras.
"""
from __future__ import annotations

import base64
import io
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

from cvgen.adapters.document_utils import parse_hex_color_int
from cvgen.adapters.pdf.cv_design_theme import THEMES
from cvgen.adapters.pdf.font_registry import FONT_MAP
from cvgen.domain.model import CvData, DesignPreferences
from cvgen.domain.ports.cv_document_generator import CvDocumentGenerator


# ---------------------------------------------------------------------------
# Utilidades internas
# ---------------------------------------------------------------------------

def _hex_to_color(hex_color: Optional[str]) -> colors.Color:
    r, g, b = parse_hex_color_int(hex_color)
    return colors.Color(r / 255.0, g / 255.0, b / 255.0)


def _wrap(text: str, max_chars: int) -> list[str]:
    """Divide ``text`` en líneas de como máximo ``max_chars`` caracteres."""
    text = text.strip()
    if not text:
        return []
    words = text.split()
    lines: list[str] = []
    current: list[str] = []
    count = 0
    for w in words:
        if count + len(w) + (1 if current else 0) > max_chars:
            lines.append(" ".join(current))
            current = [w]
            count = len(w)
        else:
            current.append(w)
            count += len(w) + (1 if len(current) > 1 else 0)
    if current:
        lines.append(" ".join(current))
    return lines


# ---------------------------------------------------------------------------
# Generador principal
# ---------------------------------------------------------------------------

class PdfCvGenerator(CvDocumentGenerator):

    def content_type(self) -> str:
        return "application/pdf"

    def file_extension(self) -> str:
        return "pdf"

    def generate(  # noqa: C901  (método largo por necesidad del layout canvas)
        self,
        cv: CvData,
        *,
        font_color: Optional[str],
        design_preferences: Optional[DesignPreferences] = None,
    ) -> bytes:
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=A4)

        # ── Resolver tema + preferencias ─────────────────────────────────────
        prefs = design_preferences or DesignPreferences()
        theme = THEMES[prefs.design_variant % len(THEMES)]

        # Tipografía: preferencia del usuario > tipografía del tema > fallback helvetica
        requested_key = prefs.font_family if prefs.font_family else theme.font_key
        font_key = requested_key if requested_key in FONT_MAP else (
            theme.font_key if theme.font_key in FONT_MAP else "helvetica"
        )
        font_reg, font_bold, font_italic = FONT_MAP[font_key]

        # Posición de foto: preferencia del usuario > tema
        photo_pos = prefs.foto_position or theme.photo_position  # "top-right"|"top-left"|"hidden"

        # Color de fondo de cabecera: preferencia del usuario > tema
        if prefs.header_bg_color:
            header_bg = _hex_to_color(prefs.header_bg_color)
        else:
            header_bg = colors.Color(*theme.header_bg)

        # Colores de texto
        accent    = _hex_to_color(font_color)
        body_text = colors.Color(0.15, 0.15, 0.15)
        muted     = colors.Color(0.45, 0.45, 0.45)

        # ── Dimensiones de la página ──────────────────────────────────────────
        width, height = A4   # 595.27 × 841.89 pts
        ML, MR = 40, 40      # márgenes laterales
        MT, MB = 30, 45      # márgenes superior / inferior
        CW = width - ML - MR  # ancho de contenido ≈ 515

        # ── CABECERA ──────────────────────────────────────────────────────────
        HDR_H   = 110
        hdr_top = height - MT       # ≈ 812
        hdr_bot = hdr_top - HDR_H   # ≈ 702

        # Fondo de la cabecera
        c.setFillColor(header_bg)
        c.rect(ML, hdr_bot, CW, HDR_H, fill=1, stroke=0)

        # Fotografía con marco sutil
        PHOTO_SIZE = 80
        PHOTO_PAD  = 3          # grosor del marco exterior
        has_photo  = False

        if photo_pos != "hidden" and cv.foto_base64:
            # Calcular coordenadas según posición
            if photo_pos == "top-left":
                photo_x = ML + 12
            else:  # top-right
                photo_x = width - MR - PHOTO_SIZE - 12

            photo_y = hdr_bot + (HDR_H - PHOTO_SIZE) / 2

            try:
                img_bytes = base64.b64decode(cv.foto_base64)
                img = ImageReader(io.BytesIO(img_bytes))
                has_photo = True

                # Marco: rectángulo blanco + borde del color acento
                c.setFillColor(colors.white)
                c.setStrokeColor(accent)
                c.setLineWidth(1.5)
                c.rect(
                    photo_x - PHOTO_PAD,
                    photo_y - PHOTO_PAD,
                    PHOTO_SIZE + PHOTO_PAD * 2,
                    PHOTO_SIZE + PHOTO_PAD * 2,
                    fill=1, stroke=1,
                )
                c.drawImage(
                    img, photo_x, photo_y,
                    width=PHOTO_SIZE, height=PHOTO_SIZE,
                    mask="auto", preserveAspectRatio=True, anchor="c",
                )
            except Exception:
                has_photo = False

        # Área de texto dentro de la cabecera
        if has_photo and photo_pos == "top-left":
            txt_x     = ML + 12 + PHOTO_SIZE + PHOTO_PAD * 2 + 12
            txt_right = width - MR - 12
        elif has_photo and photo_pos == "top-right":
            txt_x     = ML + 12
            txt_right = photo_x - 12
        else:
            txt_x     = ML + 12
            txt_right = width - MR - 12
        txt_width = txt_right - txt_x

        # Nombre (usa tamaño del tema)
        name_y = hdr_bot + HDR_H - 30
        c.setFillColor(accent)
        c.setFont(font_bold, theme.name_size)
        c.drawString(txt_x, name_y, cv.nombre)

        # Profesión
        prof_y = name_y - (theme.name_size - 2)
        c.setFillColor(body_text)
        c.setFont(font_bold, 12)
        c.drawString(txt_x, prof_y, cv.profesion)

        # Descripción breve (ajustada al ancho disponible)
        if cv.breve_descripcion:
            c.setFont(font_reg, 10)
            max_ch_desc = max(20, int(txt_width / 5.5))
            desc_y = prof_y - 15
            for line in _wrap(cv.breve_descripcion, max_chars=max_ch_desc):
                if desc_y < hdr_bot + 6:
                    break
                c.setFillColor(muted)
                c.drawString(txt_x, desc_y, line)
                desc_y -= 13

        # ── DIVISOR CABECERA / CUERPO ─────────────────────────────────────────
        # Colocado 12 pts *debajo* del borde inferior de la cabecera,
        # nunca toca el contenido de la misma.
        div_y = hdr_bot - 12
        c.setStrokeColor(accent)
        c.setLineWidth(1.5)
        c.line(ML, div_y, width - MR, div_y)

        # ── CUERPO EN DOS COLUMNAS ────────────────────────────────────────────
        COL_GAP = 18
        LEFT_W  = int(CW * 0.33)
        RIGHT_W = CW - LEFT_W - COL_GAP
        LEFT_X  = ML
        RIGHT_X = ML + LEFT_W + COL_GAP

        body_y      = div_y - 16   # ambas columnas arrancan aquí
        footer_stop = MB + 38      # las columnas no bajan de esta cota

        y_l = body_y
        y_r = body_y

        # ── COLUMNA IZQUIERDA ─────────────────────────────────────────────────

        def left_title(title: str) -> None:
            nonlocal y_l
            y_l -= 6
            c.setFillColor(accent)
            c.setFont(font_bold, 9)
            c.drawString(LEFT_X, y_l, title)
            # La línea queda 5 pts bajo la línea base (evita superposición)
            y_l -= 5
            c.setStrokeColor(accent)
            c.setLineWidth(0.7)
            c.line(LEFT_X, y_l, LEFT_X + LEFT_W, y_l)
            y_l -= 10
            c.setFillColor(body_text)
            c.setFont(font_reg, 9)

        # Contacto
        left_title("CONTACTO")
        plain_contact: list[str] = []
        if cv.contacto.email:
            plain_contact.append(cv.contacto.email)
        if cv.contacto.telefono:
            plain_contact.append(cv.contacto.telefono)
        if cv.contacto.ciudad:
            plain_contact.append(cv.contacto.ciudad)
        if cv.contacto.website:
            plain_contact.append(cv.contacto.website)

        for item in plain_contact:
            for line in _wrap(item, max_chars=29):
                if y_l > footer_stop:
                    c.drawString(LEFT_X, y_l, line)
                    y_l -= 12

        # LinkedIn — hipervínculo que muestra "LinkedIn"
        if cv.contacto.linkedin and y_l > footer_stop:
            raw = cv.contacto.linkedin.strip()
            linkedin_url = raw if raw.startswith(("http://", "https://")) else "https://" + raw
            display = "LinkedIn"
            c.setFont(font_reg, 9)
            c.setFillColor(accent)
            c.drawString(LEFT_X, y_l, display)
            link_w = c.stringWidth(display, font_reg, 9)
            # Subrayado tenue
            c.setStrokeColor(accent)
            c.setLineWidth(0.4)
            c.line(LEFT_X, y_l - 1.5, LEFT_X + link_w, y_l - 1.5)
            # Anotación de URL en el área del texto
            c.linkURL(linkedin_url, (LEFT_X, y_l - 2, LEFT_X + link_w, y_l + 9))
            c.setFillColor(body_text)
            c.setFont(font_reg, 9)
            y_l -= 12

        # Habilidades (Soft Skills)
        if cv.soft_skills:
            left_title("HABILIDADES")
            for skill in cv.soft_skills:
                if skill and y_l > footer_stop:
                    c.drawString(LEFT_X, y_l, f"• {skill}")
                    y_l -= 12

        # Intereses (Hobbies)
        if cv.hobbies:
            hobbies = [x for x in cv.hobbies if x]
            if hobbies:
                left_title("INTERESES")
                for h in hobbies:
                    if y_l > footer_stop:
                        c.drawString(LEFT_X, y_l, f"• {h}")
                        y_l -= 12

        # ── COLUMNA DERECHA ───────────────────────────────────────────────────

        def right_title(title: str) -> None:
            nonlocal y_r
            y_r -= 8
            c.setFillColor(accent)
            c.setFont(font_bold, 11)
            c.drawString(RIGHT_X, y_r, title)
            # La línea queda 6 pts bajo la línea base
            y_r -= 6
            c.setStrokeColor(accent)
            c.setLineWidth(0.7)
            c.line(RIGHT_X, y_r, RIGHT_X + RIGHT_W, y_r)
            y_r -= 13
            c.setFillColor(body_text)
            c.setFont(font_reg, 10)

        # Experiencia
        if cv.experiencia_laboral:
            right_title("EXPERIENCIA")
            for idx, e in enumerate(cv.experiencia_laboral):
                if y_r <= footer_stop:
                    break
                c.setFont(font_bold, 10)
                c.setFillColor(body_text)
                for line in _wrap(f"{e.puesto} · {e.empresa}", max_chars=52):
                    if y_r > footer_stop:
                        c.drawString(RIGHT_X, y_r, line)
                        y_r -= 13
                if y_r > footer_stop:
                    c.setFont(font_italic, 9)
                    c.setFillColor(muted)
                    c.drawString(RIGHT_X, y_r, f"{e.anio_inicio} – {e.anio_fin}")
                    y_r -= 12
                c.setFont(font_reg, 10)
                c.setFillColor(body_text)
                if e.descripcion:
                    for line in _wrap(e.descripcion, max_chars=52):
                        if y_r > footer_stop:
                            c.drawString(RIGHT_X, y_r, line)
                            y_r -= 12
                if idx < len(cv.experiencia_laboral) - 1:
                    y_r -= 8

        # Educación
        if cv.educacion:
            right_title("EDUCACIÓN")
            for idx, edu in enumerate(cv.educacion):
                if y_r <= footer_stop:
                    break
                c.setFont(font_bold, 10)
                c.setFillColor(body_text)
                for line in _wrap(edu.titulo, max_chars=52):
                    if y_r > footer_stop:
                        c.drawString(RIGHT_X, y_r, line)
                        y_r -= 13
                if y_r > footer_stop:
                    c.setFont(font_reg, 10)
                    c.drawString(
                        RIGHT_X, y_r,
                        f"{edu.institucion} · {edu.anio_inicio}–{edu.anio_fin}",
                    )
                    y_r -= 13
                if idx < len(cv.educacion) - 1:
                    y_r -= 6

        # Certificaciones
        if cv.certificaciones:
            certs: list[str] = []
            for ci in cv.certificaciones:
                label = ci.nombre
                if ci.institucion:
                    label += f" · {ci.institucion}"
                if ci.anio:
                    label += f" ({ci.anio})"
                certs.append(label)
            if certs:
                right_title("CERTIFICACIONES")
                for cert in certs:
                    if y_r <= footer_stop:
                        break
                    c.setFont(font_reg, 10)
                    c.setFillColor(body_text)
                    for line in _wrap(cert, max_chars=52):
                        if y_r > footer_stop:
                            c.drawString(RIGHT_X, y_r, line)
                            y_r -= 13
                    y_r -= 4

        # Separador vertical tenue entre columnas
        sep_x   = LEFT_X + LEFT_W + COL_GAP // 2
        sep_bot = min(y_l, y_r) - 6
        c.setStrokeColor(colors.Color(0.78, 0.78, 0.78))
        c.setLineWidth(0.5)
        c.line(sep_x, sep_bot, sep_x, body_y)

        # ── PIE DE PÁGINA ─────────────────────────────────────────────────────
        footer_line_y = MB + 22
        c.setStrokeColor(accent)
        c.setLineWidth(1)
        c.line(ML, footer_line_y, width - MR, footer_line_y)

        footer_text_y = footer_line_y - 14
        label = "DISPONIBILIDAD LABORAL: "
        c.setFillColor(accent)
        c.setFont(font_bold, 9)
        c.drawString(ML, footer_text_y, label)
        label_w = c.stringWidth(label, font_bold, 9)
        c.setFillColor(body_text)
        c.setFont(font_reg, 9)
        c.drawString(ML + label_w, footer_text_y, cv.disponibilidad_laboral)

        c.showPage()
        c.save()
        return buf.getvalue()
