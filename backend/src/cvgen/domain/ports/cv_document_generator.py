from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from cvgen.domain.model import CvData, DesignPreferences


class CvDocumentGenerator(ABC):
    @abstractmethod
    def generate(
        self,
        cv: CvData,
        *,
        font_color: Optional[str],
        design_preferences: Optional[DesignPreferences] = None,
    ) -> bytes:
        """Genera el documento en bytes (PDF o DOCX)."""

    @abstractmethod
    def content_type(self) -> str:
        """MIME type para el documento generado."""

    @abstractmethod
    def file_extension(self) -> str:
        """Extensión (por ejemplo: 'pdf' o 'docx')."""

