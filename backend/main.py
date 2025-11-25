"""FastAPI application wiring."""
from __future__ import annotations

from fastapi import FastAPI

from backend.api.routes import members, similarity, units
from backend.ingest.loader import DataLoader
from backend.ingest.sheets_client import SheetsClient
from backend.services.search import SearchService


def create_app(loader: DataLoader | None = None) -> FastAPI:
    app = FastAPI(title="Unit Search API")
    loader = loader or DataLoader(SheetsClient())
    search_service = SearchService(loader.get_connection())
    loader.reload_hooks.append(
        lambda bundle: search_service.reindex(bundle.members, bundle.member_aliases, bundle.member_generations)
    )
    app.state.loader = loader
    app.state.search_service = search_service

    app.include_router(members.router)
    app.include_router(units.router)
    app.include_router(similarity.router)
    return app


app = create_app()
