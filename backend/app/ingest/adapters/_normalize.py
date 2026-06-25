"""Shared normalization helpers for feed adapters (ICS + RSS).

Feeds hand us loosely-typed values — dates that may be naive or date-only, free-text locations,
HTML in descriptions. These helpers coerce them into the strict shapes RawEventRecord expects so
each adapter's mapping stays a thin field-copy. Kept dependency-free (stdlib only) and side-effect
free so tests can exercise them directly.
"""
from __future__ import annotations

import re
from datetime import date, datetime, time, timezone
from zoneinfo import ZoneInfo

# Mainfranken sources are local time; feeds frequently omit the timezone. Assume Europe/Berlin
# for naive timestamps so the stored `start` is unambiguous (matches the canonical Event contract).
BERLIN = ZoneInfo("Europe/Berlin")

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")
_POSTAL_RE = re.compile(r"\b(\d{5})\b")
# German calendar date, optionally with a time — e.g. "26.06.2026 18:00". Several municipal RSS
# feeds (FRIZZ) carry the real event date in the item title while pubDate is only the publish date.
_DE_DT_RE = re.compile(r"\b(\d{1,2})\.(\d{1,2})\.(\d{4})(?:\s+(\d{1,2}):(\d{2}))?")

_ONLINE_HINTS = (
    "online", "zoom", "webinar", "virtual", "livestream", "live-stream",
    "ms teams", "microsoft teams", "remote", "digital event", "stream",
)


def to_aware(value: object) -> datetime | None:
    """Coerce an ICS/RSS date value into a timezone-aware datetime, or None if unusable.

    - aware datetime  → returned unchanged
    - naive datetime  → stamped Europe/Berlin
    - date (all-day)  → midnight Europe/Berlin
    - anything else   → None (caller skips the record)
    """
    if isinstance(value, datetime):
        return value if value.tzinfo is not None else value.replace(tzinfo=BERLIN)
    if isinstance(value, date):
        return datetime.combine(value, time.min, tzinfo=BERLIN)
    return None


def from_struct_time(st: object) -> datetime | None:
    """Convert a feedparser time.struct_time (UTC) into an aware datetime, or None."""
    if st is None:
        return None
    try:
        return datetime(*st[:6], tzinfo=timezone.utc)  # type: ignore[misc]
    except (TypeError, ValueError):
        return None


def parse_de_datetime(text: object) -> datetime | None:
    """Extract the first German 'DD.MM.YYYY [HH:MM]' date in `text` as aware Europe/Berlin, else None."""
    if not text:
        return None
    m = _DE_DT_RE.search(str(text))
    if not m:
        return None
    day, month, year, hh, mm = m.groups()
    try:
        return datetime(
            int(year), int(month), int(day),
            int(hh) if hh else 0, int(mm) if mm else 0,
            tzinfo=BERLIN,
        )
    except ValueError:
        return None


def clean_text(value: object) -> str | None:
    """Strip HTML tags and collapse whitespace; return None for empty/missing input."""
    if value is None:
        return None
    text = _WS_RE.sub(" ", _TAG_RE.sub(" ", str(value))).strip()
    return text or None


def detect_online(*parts: object) -> bool:
    """True if any part mentions an online/remote venue keyword."""
    blob = " ".join(str(p) for p in parts if p).casefold()
    return any(hint in blob for hint in _ONLINE_HINTS)


def extract_postal(*parts: object) -> str | None:
    """Return the first 5-digit postal code found across the given strings, else None."""
    for part in parts:
        if not part:
            continue
        m = _POSTAL_RE.search(str(part))
        if m:
            return m.group(1)
    return None


def pick_city(location: object, cities: list[str], default: str | None) -> str | None:
    """Return the first scope city named in `location`, else the adapter default.

    Online/empty locations fall back to the default so regional sources still satisfy the geo gate.
    """
    if location:
        loc = str(location).casefold()
        for c in cities:
            if c.casefold() in loc:
                return c
    return default
