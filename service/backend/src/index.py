"""Punto de entrada FastAPI cuando el Root Directory de Vercel es `service/backend`."""

from __future__ import annotations

import sys
from pathlib import Path

_src = Path(__file__).resolve().parent
if str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

from cvgen.main import app  # noqa: E402

__all__ = ["app"]
