"""Similarity routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from backend.api.schemas import SimilarityQuery
from backend.features.similarity import top_similar

router = APIRouter()


def get_similarity_context(request: Request):
    loader = getattr(request.app.state, "loader", None)
    if not loader or not loader.get_cached_bundle():
        raise HTTPException(status_code=503, detail="data_not_loaded")
    member_ids = getattr(loader, "similarity_member_ids", [])
    matrix = getattr(loader, "similarity_matrix", None)
    if matrix is None:
        raise HTTPException(status_code=500, detail="similarity_not_ready")
    return loader, member_ids, matrix


@router.get("/similarity")
def similarity(query: SimilarityQuery = Depends(), ctx=Depends(get_similarity_context)):
    loader, member_ids, matrix = ctx
    results = top_similar(query.member_id, member_ids, matrix, top=query.top)
    return {"items": [{"member_id": mid, "score": score} for mid, score in results]}
