"""Adapter registry — the core asks here for the adapters to run.

Concrete adapters (slice 2 phase C, package .adapters) register themselves at import time via
register(). get_adapters() triggers that import lazily, so the core stays decoupled from the
concrete source modules. Empty until phase C lands its adapters.
"""
from __future__ import annotations

from .base import SourceAdapter

_REGISTRY: dict[str, SourceAdapter] = {}


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
    """Import the adapters package so its modules self-register. No-op if it does not exist yet."""
    try:
        from . import adapters  # noqa: F401  (import side-effect: registration)
    except ImportError:
        pass
