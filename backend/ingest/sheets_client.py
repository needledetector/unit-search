"""Google Sheets client helpers for ingestion."""
from __future__ import annotations

import io
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional

import pandas as pd
import requests


class MissingSheetError(RuntimeError):
    """Raised when a required sheet cannot be fetched or is empty."""


@dataclass
class SheetResult:
    name: str
    frame: pd.DataFrame


class SheetsClient:
    """Lightweight Google Sheets API client.

    This client pulls CSV exports from public sheets to avoid heavy client libraries.
    It intentionally raises :class:`MissingSheetError` when a required sheet is
    unavailable, allowing upstream callers to fail fast.
    """

    def __init__(self, session: Optional[requests.Session] = None) -> None:
        self.session = session or requests.Session()

    def _sheet_url(self, spreadsheet_id: str, sheet_name: str) -> str:
        return (
            f"https://docs.google.com/spreadsheets/d/"
            f"{spreadsheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
        )

    def fetch_sheet(self, spreadsheet_id: str, sheet_name: str) -> SheetResult:
        """Fetch a single sheet as a pandas DataFrame."""

        url = self._sheet_url(spreadsheet_id, sheet_name)
        resp = self.session.get(url)
        if resp.status_code == 404:
            raise MissingSheetError(f"missing_sheet:{sheet_name}")
        if resp.status_code >= 400:
            resp.raise_for_status()
        if not resp.text.strip():
            raise MissingSheetError(f"empty_sheet:{sheet_name}")
        frame = pd.read_csv(io.StringIO(resp.text))
        return SheetResult(name=sheet_name, frame=frame)

    def fetch_required_sheets(
        self,
        spreadsheet_id: str,
        required: Iterable[str],
        optional: Optional[Iterable[str]] = None,
    ) -> Dict[str, pd.DataFrame]:
        """Fetch required/optional sheets, raising when any required sheet is missing."""

        optional = optional or []
        tables: Dict[str, pd.DataFrame] = {}
        missing: List[str] = []

        for name in required:
            try:
                result = self.fetch_sheet(spreadsheet_id, name)
            except MissingSheetError:
                missing.append(name)
                continue
            tables[result.name] = result.frame

        if missing:
            raise MissingSheetError(f"missing_required:{','.join(sorted(missing))}")

        for name in optional:
            try:
                result = self.fetch_sheet(spreadsheet_id, name)
            except MissingSheetError:
                continue
            tables[result.name] = result.frame

        return tables
