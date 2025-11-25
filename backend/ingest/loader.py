"""Orchestration for loading Google Sheets data into application cache."""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from typing import Callable, Dict, Iterable, List, Optional

import pandas as pd

from backend.features import matrix as matrix_builder
from backend.ingest.sheets_client import MissingSheetError, SheetsClient
from backend.ingest.validators import IdConsistencyError, SchemaValidationError, ensure_references, ensure_required_columns


REQUIRED_SHEETS = ("members", "member_generations", "units", "unit_members")
OPTIONAL_SHEETS = ("member_aliases", "units_aliases")


@dataclass
class DataBundle:
    members: pd.DataFrame
    member_generations: pd.DataFrame
    units: pd.DataFrame
    unit_members: pd.DataFrame
    member_aliases: pd.DataFrame = field(default_factory=pd.DataFrame)
    units_aliases: pd.DataFrame = field(default_factory=pd.DataFrame)


class DataLoader:
    """Fetch, validate, normalize, and persist spreadsheet data."""

    def __init__(
        self,
        sheets_client: SheetsClient,
        storage_path: str = ":memory:",
        reload_hooks: Optional[List[Callable[[DataBundle], None]]] = None,
    ) -> None:
        self.sheets_client = sheets_client
        self.storage_path = storage_path
        self.conn = sqlite3.connect(storage_path)
        self.conn.row_factory = sqlite3.Row
        self.reload_hooks = reload_hooks or []
        self.cache: Optional[DataBundle] = None
        self.similarity_cache: Dict[str, List[Dict[str, float]]] = {}

    def _persist(self, bundle: DataBundle) -> None:
        # Replace existing tables
        for name, frame in (
            ("members", bundle.members),
            ("member_generations", bundle.member_generations),
            ("units", bundle.units),
            ("unit_members", bundle.unit_members),
            ("member_aliases", bundle.member_aliases),
            ("units_aliases", bundle.units_aliases),
        ):
            frame.to_sql(name, self.conn, if_exists="replace", index=False)

    def _validate(self, tables: Dict[str, pd.DataFrame]) -> DataBundle:
        for key in REQUIRED_SHEETS:
            if key not in tables:
                raise MissingSheetError(f"missing_required:{key}")

        members = tables["members"].fillna("")
        member_generations = tables["member_generations"].fillna("")
        units = tables["units"].fillna("")
        unit_members = tables["unit_members"].fillna("")
        member_aliases = tables.get("member_aliases", pd.DataFrame(columns=["member_id", "alias"]).fillna(""))
        units_aliases = tables.get("units_aliases", pd.DataFrame(columns=["unit_id", "alias", "alias_note"]).fillna(""))

        ensure_required_columns(members, ["member_id", "display_name", "alias", "branch", "status"], "members")
        ensure_required_columns(member_generations, ["member_id", "generation", "is_primary"], "member_generations")
        ensure_required_columns(units, ["unit_id", "canonical_name", "note"], "units")
        ensure_required_columns(unit_members, ["unit_id", "member_id", "weight"], "unit_members")

        member_ids = {str(v) for v in members["member_id"].fillna("") if str(v)}
        unit_ids = {str(v) for v in units["unit_id"].fillna("") if str(v)}

        ensure_references(member_generations, "member_id", member_ids, "member_generations", "members")
        ensure_references(unit_members, "member_id", member_ids, "unit_members", "members")
        ensure_references(unit_members, "unit_id", unit_ids, "unit_members", "units")
        ensure_references(member_aliases, "member_id", member_ids, "member_aliases", "members")
        ensure_references(units_aliases, "unit_id", unit_ids, "units_aliases", "units")

        # normalize weights
        unit_members = unit_members.copy()
        unit_members["weight"] = pd.to_numeric(unit_members["weight"], errors="coerce").fillna(9999)

        return DataBundle(
            members=members,
            member_generations=member_generations,
            units=units,
            unit_members=unit_members,
            member_aliases=member_aliases,
            units_aliases=units_aliases,
        )

    def _recompute_similarity(self, bundle: DataBundle) -> None:
        member_ids, _, mat = matrix_builder.build_member_unit_matrix(bundle.unit_members)
        self.similarity_matrix = mat
        self.similarity_member_ids = member_ids
        self.similarity_cache = {}

    def load(self, spreadsheet_id: str) -> DataBundle:
        tables = self.sheets_client.fetch_required_sheets(
            spreadsheet_id, REQUIRED_SHEETS, OPTIONAL_SHEETS
        )
        return self.load_from_frames(tables)

    def load_from_frames(self, tables: Dict[str, pd.DataFrame]) -> DataBundle:
        bundle = self._validate(tables)
        self._persist(bundle)
        self.cache = bundle
        self._recompute_similarity(bundle)
        for hook in self.reload_hooks:
            hook(bundle)
        return bundle

    def get_connection(self) -> sqlite3.Connection:
        return self.conn

    def get_cached_bundle(self) -> Optional[DataBundle]:
        return self.cache
