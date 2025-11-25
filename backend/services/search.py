"""Search service backed by SQLite FTS5."""
from __future__ import annotations

import sqlite3
from typing import Dict, Iterable, List, Optional

import pandas as pd

from backend.api.schemas import MemberSearchQuery


class SearchService:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn
        self.member_meta: Dict[str, Dict] = {}
        self.member_generations: Dict[str, set] = {}
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        self.conn.execute(
            "CREATE VIRTUAL TABLE IF NOT EXISTS member_fts USING fts5(member_id, content)"
        )

    def reindex(self, members: pd.DataFrame, member_aliases: pd.DataFrame, member_generations: pd.DataFrame) -> None:
        self.conn.execute("DELETE FROM member_fts")
        self.member_meta.clear()
        self.member_generations.clear()

        alias_map = member_aliases.groupby("member_id")["alias"].apply(list).to_dict()
        gen_map = (
            member_generations.groupby("member_id")["generation"].apply(lambda s: set(s.dropna().astype(str))).to_dict()
        )

        for _, row in members.iterrows():
            mid = str(row.get("member_id"))
            alias = str(row.get("alias", ""))
            display = str(row.get("display_name", mid))
            branch = str(row.get("branch", ""))
            status = str(row.get("status", ""))
            aliases = alias_map.get(mid, [])
            content_parts = [display, alias] + aliases
            content = " ".join([c for c in content_parts if c])
            self.conn.execute(
                "INSERT INTO member_fts(member_id, content) VALUES (?, ?)",
                (mid, content),
            )
            self.member_meta[mid] = {
                "member_id": mid,
                "display_name": display,
                "alias": alias,
                "branch": branch,
                "status": status,
            }
            self.member_generations[mid] = gen_map.get(mid, set())
        self.conn.commit()

    def search(self, query: MemberSearchQuery) -> List[Dict]:
        sql = "SELECT member_id, bm25(member_fts) as rank FROM member_fts"
        params: List = []
        where_clause = ""
        if query.keyword:
            where_clause = " WHERE member_fts MATCH ?"
            params.append(query.keyword)
        order_clause = " ORDER BY rank"
        limit_clause = " LIMIT ? OFFSET ?"
        params.extend([query.limit, query.offset])
        cursor = self.conn.execute(sql + where_clause + order_clause + limit_clause, params)
        member_ids = [row[0] for row in cursor.fetchall()]
        if not query.keyword:
            member_ids = list(self.member_meta.keys())
        return self._apply_filters(member_ids, query)

    def _apply_filters(self, member_ids: Iterable[str], query: MemberSearchQuery) -> List[Dict]:
        filtered: List[Dict] = []
        branches = set(query.branch or [])
        statuses = set(query.status or [])
        generations = set(query.generation or [])
        for mid in member_ids:
            meta = self.member_meta.get(mid)
            if not meta:
                continue
            if branches and meta.get("branch") not in branches:
                continue
            if statuses and meta.get("status") not in statuses:
                continue
            if generations and not (self.member_generations.get(mid, set()) & generations):
                continue
            filtered.append(meta)
        return filtered
