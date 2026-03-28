"""Punto de entrada FastAPI para Vercel (expone `app` en la ruta esperada por la plataforma)."""

from __future__ import annotations

import sys
from pathlib import Path

_backend_src = Path(__file__).resolve().parent.parent / "service" / "backend" / "src"
sys.path.insert(0, str(_backend_src))

from cvgen.main import app  # noqa: E402

__all__ = ["app"]
