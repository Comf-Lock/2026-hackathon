"""Time helpers shared across the app — one UTC clock so "now" means the same everywhere.

``utcnow`` was previously redefined in several modules (models, ingest core); this is the single
source. Always timezone-aware UTC, so stored timestamps and comparisons never mix naive/aware.
"""
from __future__ import annotations

from datetime import datetime, timezone


def utcnow() -> datetime:
    """Timezone-aware current time in UTC — the canonical default for timestamp fields."""
    return datetime.now(timezone.utc)
