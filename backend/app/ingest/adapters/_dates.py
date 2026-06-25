"""Small date/timezone helpers shared by the adapters.

Events in the catalogue are local (Europe/Berlin). Sources give us three shapes:
- full ISO 8601 with offset (Meetup: "2026-06-26T10:00:00+02:00") -> parse as-is,
- ISO date only (Eventbrite: "2026-06-26") -> midnight Europe/Berlin,
- German "DD.MM.YYYY[, HH:MM]" (THWS) -> parsed here.
All return tz-aware datetimes so the canonical store keeps a stable instant.
"""
from __future__ import annotations

from datetime import datetime, time
from zoneinfo import ZoneInfo

BERLIN = ZoneInfo("Europe/Berlin")


def from_iso(value: str) -> datetime:
    """Parse an ISO 8601 string; assume Europe/Berlin when the value carries no offset."""
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=BERLIN)
    return dt


def from_iso_date(value: str) -> datetime:
    """Parse a bare ISO date (YYYY-MM-DD) as midnight Europe/Berlin."""
    d = datetime.fromisoformat(value).date()
    return datetime.combine(d, time(0, 0), tzinfo=BERLIN)


def from_german(date_str: str, time_str: str | None = None) -> datetime:
    """Parse 'DD.MM.YYYY' (+ optional 'HH:MM') as Europe/Berlin."""
    day, month, year = (int(p) for p in date_str.split("."))
    hour, minute = 0, 0
    if time_str:
        hour, minute = (int(p) for p in time_str.split(":"))
    return datetime(year, month, day, hour, minute, tzinfo=BERLIN)
