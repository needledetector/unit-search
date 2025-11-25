"""Lightweight stub of pydantic for offline testing."""
from __future__ import annotations

from typing import Any


class BaseModel:
    def __init__(self, **data: Any) -> None:
        # apply class defaults first
        for key in getattr(self, "__annotations__", {}):
            if hasattr(self.__class__, key):
                setattr(self, key, getattr(self.__class__, key))
        for key, value in data.items():
            setattr(self, key, value)

    def dict(self) -> dict:
        return self.__dict__.copy()


def Field(default: Any = None, **_: Any) -> Any:
    return default
