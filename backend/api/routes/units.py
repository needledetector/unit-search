"""Unit routes."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

router = APIRouter()


@router.get("/units/{unit_id}")
def get_unit(unit_id: str, request: Request):
    loader = getattr(request.app.state, "loader", None)
    if not loader or not loader.get_cached_bundle():
        raise HTTPException(status_code=503, detail="data_not_loaded")
    bundle = loader.get_cached_bundle()
    assert bundle
    units = bundle.units
    unit_members = bundle.unit_members

    unit_row = units.loc[units["unit_id"].astype(str) == str(unit_id)]
    if unit_row.empty:
        raise HTTPException(status_code=404, detail="unit_not_found")
    unit_dict = unit_row.iloc[0].to_dict()

    members = unit_members[unit_members["unit_id"].astype(str) == str(unit_id)]
    members = members.sort_values(by="weight", ascending=True)
    member_list = [
        {"member_id": row.member_id, "weight": float(row.weight)} for row in members.itertuples(index=False)
    ]
    unit_dict["members"] = member_list
    return unit_dict
