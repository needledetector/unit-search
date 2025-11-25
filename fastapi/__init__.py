"""Minimal FastAPI-compatible stubs for offline execution."""
from __future__ import annotations

import inspect
from types import SimpleNamespace
from typing import Any, Callable, Dict, List, Optional


class HTTPException(Exception):
    def __init__(self, status_code: int, detail: Any = None) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


class Request:
    def __init__(self, app: Any) -> None:
        self.app = app


class Depends:
    def __init__(self, dependency: Optional[Callable[..., Any]] = None) -> None:
        self.dependency = dependency


class Route:
    def __init__(self, path: str, func: Callable) -> None:
        self.path = path
        self.func = func


class APIRouter:
    def __init__(self) -> None:
        self.routes: List[Route] = []

    def get(self, path: str):
        def decorator(func: Callable) -> Callable:
            self.routes.append(Route(path, func))
            return func

        return decorator


class FastAPI:
    def __init__(self, title: str = "FastAPI") -> None:
        self.routes: List[Route] = []
        self.state = SimpleNamespace()
        self.title = title

    def include_router(self, router: APIRouter) -> None:
        self.routes.extend(router.routes)

    def get(self, path: str):
        def decorator(func: Callable) -> Callable:
            self.routes.append(Route(path, func))
            return func

        return decorator


# Test client implementation
from fastapi.testclient import TestClient  # noqa: E402

__all__ = [
    "APIRouter",
    "Depends",
    "FastAPI",
    "HTTPException",
    "Request",
    "TestClient",
]
