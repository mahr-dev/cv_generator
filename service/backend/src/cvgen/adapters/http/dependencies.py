from __future__ import annotations

from typing import Dict

from cvgen.adapters.docx.docx_cv_generator import DocxCvGenerator
from cvgen.adapters.mongo.mongo_usage_repository import build_mongo_usage_repository
from cvgen.adapters.pdf.pdf_cv_generator import PdfCvGenerator
from cvgen.application.generate_cv_use_case import GenerateCvUseCase
from cvgen.domain.model import CvData
from cvgen.domain.ports.cv_document_generator import CvDocumentGenerator


def build_generate_cv_use_case() -> GenerateCvUseCase:
    usage_repository = build_mongo_usage_repository()
    document_generators: Dict[str, CvDocumentGenerator] = {
        "pdf": PdfCvGenerator(),
        "docx": DocxCvGenerator(),
    }
    return GenerateCvUseCase(
        usage_repository=usage_repository,
        document_generators=document_generators,
    )

