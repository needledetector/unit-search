"""Validation helpers for ingested sheet data."""
from __future__ import annotations

from typing import Iterable, Set

import pandas as pd


class SchemaValidationError(ValueError):
    """Raised when required columns are missing."""


class IdConsistencyError(ValueError):
    """Raised when foreign keys reference missing ids."""


def ensure_required_columns(frame: pd.DataFrame, required: Iterable[str], label: str) -> None:
    missing = [col for col in required if col not in frame.columns]
    if missing:
        raise SchemaValidationError(f"missing_columns:{label}:{','.join(sorted(missing))}")


def ensure_references(
    frame: pd.DataFrame,
    column: str,
    allowed_ids: Set[str],
    label: str,
    target_label: str,
) -> None:
    """Ensure that every id in ``frame[column]`` exists in ``allowed_ids``."""

    if column not in frame.columns:
        raise SchemaValidationError(f"missing_columns:{label}:{column}")

    invalid = sorted({str(v) for v in frame[column].fillna("") if str(v) not in allowed_ids and str(v) != ""})
    if invalid:
        raise IdConsistencyError(
            f"invalid_reference:{label}:{column}:{','.join(invalid)}->${target_label}"
        )
