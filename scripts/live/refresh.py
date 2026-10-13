"""Refresh the live data (GitHub languages) with last-known-good fallback.

Preference: fresh fetch → cached data from an earlier successful run (same
user only) → placeholder image. Nothing ever renders as an error image.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from ..config import Config
from . import github
from .http import HTTP, FetchError

CACHE_VERSION = 2


@dataclass
class Source:
    data: dict | None
    fetched: str | None   # ISO timestamp of the data's last successful fetch
    fresh: bool           # fetched during this run


def load_cache(path: Path | None) -> dict:
    empty = {"version": CACHE_VERSION, "sources": {}}
    if not path or not path.exists():
        return empty
    try:
        cache = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return empty
    if cache.get("version") != CACHE_VERSION or not isinstance(cache.get("sources"), dict):
        return empty
    return cache


def refresh(cfg: Config, cache: dict, *, offline: bool, http: HTTP | None = None, token: str | None = None,
            now: datetime | None = None, log=print) -> tuple[dict, Source]:
    now = now or datetime.now(timezone.utc).replace(microsecond=0)
    stamp = now.isoformat().replace("+00:00", "Z")
    old = cache.get("sources", {}).get("github")
    if old and str((old.get("data") or {}).get("handle", "")).lower() != cfg.github_username.lower():
        old = None  # cached data belongs to another account
    data, fetched, fresh = None, None, False
    if not offline:
        try:
            if not token:
                raise FetchError("no GITHUB_TOKEN available")
            data = github.fetch(cfg.github_username, token, http or HTTP(
                user_agent=f"profile-readme (+https://github.com/{cfg.github_username})"))
            fetched, fresh = stamp, True
            log("  [live]  github languages: ok")
        except FetchError as exc:
            log(f"  [cache] github languages: fetch failed ({exc})")
        except (KeyError, TypeError, ValueError) as exc:  # a changed API shape
            log(f"  [cache] github languages: unexpected data ({type(exc).__name__}: {exc})")
    if data is None and old:
        data, fetched = old.get("data"), old.get("fetched")
        log(f"  [cache] github languages: using data from {fetched}")
    elif data is None:
        log("  [none]  github languages: no data yet (placeholder shown)")
    out = {"version": CACHE_VERSION, "updated": stamp, "sources": {}}
    if data is not None:
        out["sources"]["github"] = {"fetched": fetched, "data": data}
    return out, Source(data, fetched, fresh)


def save_cache(cache: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cache, indent=1, sort_keys=True) + "\n", encoding="utf-8")
