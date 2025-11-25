"""Member search routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from backend.api.schemas import MemberSearchQuery

router = APIRouter()


def get_search_service(request: Request):
    service = getattr(request.app.state, "search_service", None)
    loader = getattr(request.app.state, "loader", None)
    if not loader or not loader.get_cached_bundle():
        raise HTTPException(status_code=503, detail="data_not_loaded")
    if not service:
        raise HTTPException(status_code=500, detail="search_service_unavailable")
    return service


@router.get("/members/search")
def search_members(query: MemberSearchQuery = Depends(), service=Depends(get_search_service)):
    return {"items": service.search(query)}
