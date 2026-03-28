from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class UsageRepository(ABC):
    @abstractmethod
    def log_usage(
        self,
        *,
        ip: str,
        user_agent: str,
        output_format: str,
        font_color: Optional[str],
        payload: Dict[str, Any],
    ) -> None:
        """Registra el uso de la API (best-effort)."""

