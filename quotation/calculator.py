"""TODO_FACTORY_GENERATION: HansePack quotation calculation module.

This scaffold will be replaced by the Software Factory delivery workflow (WF-QUOTATION02-S6-001).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


class QuotationValidationError(ValueError):
    """Raised when quotation input fails validation."""

    def __init__(self, message: str, reason: str = "validation_error") -> None:
        super().__init__(message)
        self.reason = reason


def load_catalogue(
    catalogue_path: str | Path | None = None,
) -> dict[str, dict[str, Any]]:
    """Load the HansePack product catalogue."""
    raise NotImplementedError("TODO_FACTORY_GENERATION")


def calculate_quotation(
    items: list[dict[str, Any]],
    *,
    catalogue_path: str | Path | None = None,
    rule_version: str = "HP-V1",
) -> dict[str, Any]:
    """Calculate a deterministic HansePack quotation."""
    raise NotImplementedError("TODO_FACTORY_GENERATION")
