"""Adapter registry — the core asks here for the adapters to run.

Two registration sources feed it:
- Code adapters (package .adapters) self-register at import time via register(); _load_adapters()
  triggers that import lazily so the core stays decoupled from the concrete source modules.
- Config feeds (ingest/feeds.yaml) are registered as generic ICS/RSS adapters by feed_loader; that
  load is guarded to read the YAML once.

DB feeds (feed_sources table) are layered on top per ingest run by the core, which has a session.
"""
from __future__ import annotations

import logging

from .base import SourceAdapter

logger = logging.getLogger("eventradar.ingest.registry")

_REGISTRY: dict[str, SourceAdapter] = {}
_config_feeds_loaded = False


def register(adapter: SourceAdapter) -> SourceAdapter:
    """Register an adapter instance under its .name (idempotent — re-register overwrites)."""
    _REGISTRY[adapter.name] = adapter
    return adapter


def get_adapters(names: list[str] | None = None) -> list[SourceAdapter]:
    """Return registered adapters, optionally filtered to `names` (preserving that order)."""
    _load_adapters()
    if names:
        return [_REGISTRY[n] for n in names if n in _REGISTRY]
    return list(_REGISTRY.values())


def _load_adapters() -> None:
    """Self-register code adapters (import side-effect) + config feeds (once). Failures are non-fatal."""
    global _config_feeds_loaded
    try:
        from . import adapters  # noqa: F401  (import side-effect: registration)
    except ImportError:
        pass
    if not _config_feeds_loaded:
        try:
            from .feed_loader import register_config_feeds

            register_config_feeds()
        except Exception as exc:  # a broken config must not block the code adapters
            logger.warning("config feed load failed: %s", exc)
        _config_feeds_loaded = True
