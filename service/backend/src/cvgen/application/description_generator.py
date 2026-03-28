from __future__ import annotations

from cvgen.domain.model import CvData


class DescriptionGenerator:
    def generate(self, cv: CvData) -> str:
        # Generador simple “estático”: minimalista y fácil de mantener.
        soft = ", ".join([s for s in cv.soft_skills[:3] if s])
        exp_titles = [e.puesto for e in cv.experiencia_laboral if e.puesto]
        exp = ", ".join(exp_titles[:2]) if exp_titles else "experiencia profesional"

        parts = [
            f"Profesional en {cv.profesion}.",
            f"Experiencia destacada en {exp}.",
        ]
        if soft:
            parts.append(f"Fortalezas: {soft}.")
        return " ".join(parts)

