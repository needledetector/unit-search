import os
import sys

ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import pandas as pd
import pytest

from backend.ingest.sheets_client import MissingSheetError, SheetsClient
from backend.ingest.validators import IdConsistencyError, SchemaValidationError, ensure_references, ensure_required_columns


class DummyResponse:
    def __init__(self, status_code=200, text=""):
        self.status_code = status_code
        self.text = text
        self.headers = {}

    def raise_for_status(self):
        raise RuntimeError(f"status:{self.status_code}")


class DummySession:
    def __init__(self, responses):
        self.responses = responses
        self.calls = []

    def get(self, url):
        self.calls.append(url)
        return self.responses.pop(0)


def test_missing_sheet_raises():
    session = DummySession([DummyResponse(status_code=404)])
    client = SheetsClient(session=session)
    with pytest.raises(MissingSheetError):
        client.fetch_required_sheets("spreadsheet", ["members"])


def test_required_columns_and_id_checks():
    df = pd.DataFrame({"col1": [1]})
    with pytest.raises(SchemaValidationError):
        ensure_required_columns(df, ["col1", "col2"], "sample")

    members = pd.DataFrame({"member_id": ["a"]})
    refs = pd.DataFrame({"member_id": ["a", "b"]})
    with pytest.raises(IdConsistencyError):
        ensure_references(refs, "member_id", {"a"}, "refs", "members")
