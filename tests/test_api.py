import os
import sys

ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import pandas as pd
from fastapi.testclient import TestClient

from backend.ingest.loader import DataLoader
from backend.ingest.sheets_client import SheetsClient
from backend.main import create_app


def build_tables():
    members = pd.DataFrame(
        [
            {"member_id": "m1", "display_name": "Alice", "alias": "Al", "branch": "A", "status": "active"},
            {"member_id": "m2", "display_name": "Bob", "alias": "Bobby", "branch": "B", "status": "retired"},
            {"member_id": "m3", "display_name": "Carol", "alias": "", "branch": "A", "status": "active"},
        ]
    )
    member_generations = pd.DataFrame(
        [
            {"member_id": "m1", "generation": "1", "is_primary": True},
            {"member_id": "m2", "generation": "1", "is_primary": True},
            {"member_id": "m3", "generation": "2", "is_primary": True},
        ]
    )
    units = pd.DataFrame(
        [
            {"unit_id": "u1", "canonical_name": "Unit One", "note": ""},
            {"unit_id": "u2", "canonical_name": "Unit Two", "note": ""},
        ]
    )
    unit_members = pd.DataFrame(
        [
            {"unit_id": "u1", "member_id": "m1", "weight": 1},
            {"unit_id": "u1", "member_id": "m2", "weight": 2},
            {"unit_id": "u2", "member_id": "m1", "weight": 3},
            {"unit_id": "u2", "member_id": "m3", "weight": 1},
        ]
    )
    member_aliases = pd.DataFrame(
        [
            {"member_id": "m1", "alias": "A-chan"},
            {"member_id": "m3", "alias": "Sea"},
        ]
    )
    units_aliases = pd.DataFrame(columns=["unit_id", "alias", "alias_note"])
    return {
        "members": members,
        "member_generations": member_generations,
        "units": units,
        "unit_members": unit_members,
        "member_aliases": member_aliases,
        "units_aliases": units_aliases,
    }


def prepare_client():
    loader = DataLoader(SheetsClient())
    app = create_app(loader)
    loader.load_from_frames(build_tables())
    return TestClient(app)


def test_member_search_filters_branch():
    client = prepare_client()
    resp = client.get("/members/search", params={"branch": ["A"]})
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert all(item["branch"] == "A" for item in items)


def test_member_search_keyword_matches_alias():
    client = prepare_client()
    resp = client.get("/members/search", params={"keyword": "Sea"})
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert any(item["member_id"] == "m3" for item in items)


def test_unit_members_sorted_by_weight():
    client = prepare_client()
    resp = client.get("/units/u1")
    assert resp.status_code == 200
    data = resp.json()
    weights = [m["weight"] for m in data["members"]]
    assert weights == sorted(weights)


def test_similarity_endpoint_returns_results():
    client = prepare_client()
    resp = client.get("/similarity", params={"member_id": "m1", "top": 2})
    assert resp.status_code == 200
    data = resp.json()["items"]
    assert len(data) == 2
    ids = [item["member_id"] for item in data]
    assert "m2" in ids and "m3" in ids
