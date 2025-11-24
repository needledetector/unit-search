from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional

_LOCALES_CACHE: Dict[str, Dict[str, str]] = {}


def _load_locale(lang: str) -> Dict[str, str]:
    if lang in _LOCALES_CACHE:
        return _LOCALES_CACHE[lang]
    base = Path(__file__).parent / "locales"
    p = base / f"{lang}.json"
    if not p.exists():
        _LOCALES_CACHE[lang] = {}
        return _LOCALES_CACHE[lang]
    with p.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    _LOCALES_CACHE[lang] = data
    return data


def t(key: str, lang: str, default: Optional[str] = None) -> str:
    """Return translated string for `key` in `lang`.

    Simple lookup with dot-separated keys. Falls back to `default` or the
    key itself if translation not found.
    """
    data = _load_locale(lang)
    # support nested keys separated by dots
    parts = key.split(".")
    cur = data
    for p in parts:
        if isinstance(cur, dict) and p in cur:
            cur = cur[p]
        else:
            return default if default is not None else key
    return cur if isinstance(cur, str) else (default if default is not None else key)
