"""Adapter registry — the single, deterministic source of the adapters to run.

`get_adapters(session)` composes the full set in **one call, every call**, from three layers:

- Code adapters (package ``.adapters``) self-register at import time via ``register()``.
- Config feeds (``feeds.yaml``) are built fresh by ``feed_loader.build_config_feeds()``.
- DB feeds (``feed_sources`` table) are built by ``feed_loader.build_db_feeds(session)`` — only when a
  session is given — and layered last, so a DB feed re-using a name wins (DB > config > code).

There is no "have the config feeds loaded yet?" latch and no ordering rule for callers: ask and the
composition is rebuilt deterministically. ``feed_loader`` is imported lazily inside ``get_adapters``
and never imports ``registry`` back, so the two modules form a clean one-directional dependency.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from .base import SourceAdapter

if TYPE_CHECKING:  # avoid importing the DB layer at module load
    from sqlmodel import Session

logger = logging.getLogger("eventradar.ingest.registry")

# Code adapters self-register here at import time (import side-effect in the .adapters submodules).
_CODE_ADAPTERS: dict[str, SourceAdapter] = {}


def register(adapter: SourceAdapter) -> SourceAdapter:
    """Register a code adapter under its ``.name`` (idempotent — re-register overwrites)."""
    _CODE_ADAPTERS[adapter.name] = adapter
    return adapter


def _code_adapters() -> list[SourceAdapter]:
    """Import the code-adapter package (registration side-effect) and return the registered set."""
    try:
        from . import adapters  # noqa: F401  (import side-effect: registration)
    except ImportError:
        pass
    return list(_CODE_ADAPTERS.values())


def get_adapters(
    session: Session | None = None,
    names: list[str] | None = None,
) -> list[SourceAdapter]:
    """Build the full adapter set deterministically, then optionally filter to ``names``.

    Layers are composed in order — code adapters, then config feeds, then (only if ``session`` is
    given) DB feeds — so a later layer re-using a name wins (DB > config > code). Pass a session to
    include DB feeds; omit it for the code + config view (unit tests, ``list`` without a database).

    With ``names`` the result is filtered to those names, preserving the requested order; unknown
    names are silently dropped.
    """
    from .feed_loader import build_config_feeds, build_db_feeds

    merged: dict[str, SourceAdapter] = {}
    for adapter in _code_adapters():
        merged[adapter.name] = adapter
    for adapter in build_config_feeds():
        merged[adapter.name] = adapter
    if session is not None:
        for adapter in build_db_feeds(session):
            merged[adapter.name] = adapter

    if names:
        return [merged[n] for n in names if n in merged]
    return list(merged.values())
