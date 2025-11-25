"""API schema definitions."""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class MemberSearchQuery(BaseModel):
    keyword: Optional[str] = Field(default=None, description="Keyword for FTS search")
    branch: Optional[List[str]] = Field(default=None)
    status: Optional[List[str]] = Field(default=None)
    generation: Optional[List[str]] = Field(default=None)
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class SimilarityQuery(BaseModel):
    member_id: str
    top: int = Field(default=5, ge=1, le=50)
