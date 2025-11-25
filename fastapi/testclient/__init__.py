"""Tiny TestClient stub to exercise routes without external deps."""
from __future__ import annotations

import inspect
import typing
from typing import Any, Dict, Optional

from fastapi import Depends, HTTPException, Request


class Response:
    def __init__(self, status_code: int, json_data: Any = None):
        self.status_code = status_code
        self._json = json_data

    def json(self):
        return self._json


class TestClient:
    def __init__(self, app):
        self.app = app

    def _match_route(self, path: str):
        for route in self.app.routes:
            if "{" not in route.path:
                if route.path == path:
                    return route, {}
            else:
                # simple path param extraction
                prefix = route.path.split("{")[0]
                if path.startswith(prefix):
                    key = route.path.split("{")[1].split("}")[0]
                    value = path[len(prefix) :]
                    return route, {key: value}
        return None, {}

    def _resolve_kwargs(self, func, params: Dict[str, Any], path_params: Dict[str, Any]):
        kwargs = {}
        sig = inspect.signature(func)
        hints = typing.get_type_hints(func)
        for name, param in sig.parameters.items():
            if name in path_params:
                kwargs[name] = path_params[name]
                continue
            default = param.default
            if isinstance(default, Depends):
                dep = default.dependency
                if dep is None:
                    anno = hints.get(name)
                    if anno:
                        kwargs[name] = anno(**params)
                elif dep:
                    kwargs[name] = dep(Request(self.app))
            else:
                anno = hints.get(name)
                if anno is Request:
                    kwargs[name] = Request(self.app)
                elif anno:
                    try:
                        kwargs[name] = anno(**params)
                    except Exception:
                        kwargs[name] = params.get(name)
                else:
                    kwargs[name] = params.get(name)
        return kwargs

    def get(self, path: str, params: Optional[Dict[str, Any]] = None):
        params = params or {}
        route, path_params = self._match_route(path)
        if not route:
            return Response(404, json_data={"detail": "not_found"})
        try:
            kwargs = self._resolve_kwargs(route.func, params, path_params)
            result = route.func(**kwargs)
            return Response(200, json_data=result)
        except HTTPException as exc:
            return Response(exc.status_code, json_data={"detail": exc.detail})
