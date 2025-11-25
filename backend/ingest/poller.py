"""Poller to detect spreadsheet updates and trigger reloads."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Callable, Optional

import requests

logger = logging.getLogger(__name__)


@dataclass
class PollResult:
    changed: bool
    etag: Optional[str]


class SpreadsheetPoller:
    def __init__(self, session: Optional[requests.Session] = None) -> None:
        self.session = session or requests.Session()
        self.last_etag: Optional[str] = None

    def check(self, spreadsheet_id: str) -> PollResult:
        url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit"
        resp = self.session.head(url)
        if resp.status_code >= 400:
            resp.raise_for_status()
        etag = resp.headers.get("ETag")
        changed = etag is not None and etag != self.last_etag
        if changed:
            logger.info("Spreadsheet %s changed (etag=%s)", spreadsheet_id, etag)
        self.last_etag = etag or self.last_etag
        return PollResult(changed=changed, etag=etag)

    def start_polling(self, spreadsheet_id: str, on_change: Callable[[], None]) -> None:
        if self.check(spreadsheet_id).changed:
            on_change()
