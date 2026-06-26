"""Attendance / RSVP popularity signal.

Derives a *real* attendee count per event from the **source platform's own RSVP numbers** — not
from web-wide mention scraping (that was deliberately rejected). Two providers, both graceful:

- **Luma** — the public event page exposes ``guest_count`` without auth. We fetch the page and read
  the number. No key needed.
- **Meetup** — the "going" RSVP count. Preferred straight from the **already-scraped** page: the
  Meetup adapter stashes ``going_count`` on ``EventSource.raw_payload`` (see adapters/meetup.py), so
  no key is needed for sources we already crawl. Only when that number is absent do we fall back to
  Meetup's GraphQL API, which needs ``MEETUP_API_KEY``. With no key and no scraped number, Meetup
  simply contributes nothing — no crash.

The design mirrors enrichment.score: the network boundary is isolated to ``_fetch_url`` /
``_fetch_meetup_going_via_api`` (tests mock *these*; the suite never makes a real call), and
everything else is pure and unit-tested. ``attendance_for_event`` orchestrates + persists; it is
idempotent — an unchanged count re-stamps ``attendance_checked_at`` and reports ``unchanged``, and
the CLI default scopes to events not yet checked so re-runs do not re-hit the network.
"""
from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone

from ..config import settings

logger = logging.getLogger(__name__)

# Meetup GraphQL endpoint — only ever called when a token is configured.
_MEETUP_GQL_URL = "https://api.meetup.com/gql"

_NEXT_RE = re.compile(
    r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', re.S
)
# Keys a Luma payload may use for its public attendee count, in priority order.
_LUMA_COUNT_KEYS = ("guest_count", "approved_guest_count", "going_count")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# --- pure extractors -----------------------------------------------------------------------


def meetup_going_from_payload(raw_payload: object) -> int | None:
    """The Meetup 'going' count captured while scraping (no API key). Pure.

    The adapter writes ``{"going_count": N}`` onto the EventSource's ``raw_payload`` whenever the
    scraped page exposed it; here we read it back defensively."""
    if not isinstance(raw_payload, dict):
        return None
    val = raw_payload.get("going_count")
    return val if isinstance(val, int) and val >= 0 else None


def _search_count(obj: object) -> int | None:
    """Depth-first search for the first Luma guest-count key with a non-negative int value."""
    if isinstance(obj, dict):
        for key in _LUMA_COUNT_KEYS:
            val = obj.get(key)
            if isinstance(val, int) and val >= 0:
                return val
        for val in obj.values():
            found = _search_count(val)
            if found is not None:
                return found
    elif isinstance(obj, list):
        for val in obj:
            found = _search_count(val)
            if found is not None:
                return found
    return None


def parse_luma_guest_count(text: str | None) -> int | None:
    """Extract the public guest count from a Luma event page. Pure (no network).

    Tries the embedded ``__NEXT_DATA__`` JSON first (Luma is a Next.js app), then a raw-regex
    fallback so a markup change that moves the JSON around still yields a number."""
    if not text:
        return None
    match = _NEXT_RE.search(text)
    if match:
        try:
            data = json.loads(match.group(1))
        except json.JSONDecodeError:
            data = None
        if data is not None:
            found = _search_count(data)
            if found is not None:
                return found
    fallback = re.search(r'"(?:approved_)?guest_count"\s*:\s*(\d+)', text)
    return int(fallback.group(1)) if fallback else None


def _meetup_event_id(external_id: str | None) -> str | None:
    """Numeric Meetup event id from a stored external_id like ``meetup:315082274``."""
    if not external_id:
        return None
    tail = external_id.split(":", 1)[-1].strip()
    return tail or None


# --- source classification -----------------------------------------------------------------


def is_luma_source(source) -> bool:
    url = (getattr(source, "source_url", "") or "").lower()
    return getattr(source, "source_adapter", "") == "luma" or "lu.ma" in url


def is_meetup_source(source) -> bool:
    url = (getattr(source, "source_url", "") or "").lower()
    return getattr(source, "source_adapter", "") == "meetup" or "meetup.com" in url


# --- network boundary (mocked in tests) ----------------------------------------------------


def _fetch_url(url: str) -> str | None:
    """GET a page and return its text, or None on any error. THE network boundary — tests mock this."""
    import httpx

    from ..ingest.http import HEADERS, TIMEOUT

    try:
        with httpx.Client(headers=HEADERS, timeout=TIMEOUT, follow_redirects=True) as cli:
            resp = cli.get(url)
            resp.raise_for_status()
            return resp.text
    except Exception:  # noqa: BLE001 — a single source failure must never abort the batch
        logger.warning("attendance: luma fetch failed for %s", url, exc_info=True)
        return None


def _fetch_meetup_going_via_api(event_id: str, token: str) -> int | None:
    """Query Meetup's GraphQL API for an event's 'going' count. Only called when a token is set.

    Network boundary — tests mock this; it is never reached without ``MEETUP_API_KEY``."""
    import httpx

    from ..ingest.http import TIMEOUT

    query = "query($id: ID!) { event(id: $id) { going { totalCount } } }"
    try:
        with httpx.Client(timeout=TIMEOUT) as cli:
            resp = cli.post(
                _MEETUP_GQL_URL,
                json={"query": query, "variables": {"id": event_id}},
                headers={"Authorization": f"Bearer {token}"},
            )
            resp.raise_for_status()
            data = resp.json()
        total = data["data"]["event"]["going"]["totalCount"]
        return total if isinstance(total, int) and total >= 0 else None
    except Exception:  # noqa: BLE001 — isolate API failures
        logger.warning("attendance: meetup API fetch failed for %s", event_id, exc_info=True)
        return None


# --- orchestration -------------------------------------------------------------------------


def _resolve_count(sources: list) -> tuple[int | None, str | None]:
    """Pick the best attendee count across an event's sources. Pure-ish (delegates I/O to mocks).

    Priority: Luma public count → Meetup scraped 'going' → Meetup GraphQL (only with a key)."""
    luma = [s for s in sources if is_luma_source(s)]
    meetup = [s for s in sources if is_meetup_source(s)]

    # 1. Luma — public, authless.
    for src in luma:
        count = parse_luma_guest_count(_fetch_url(src.source_url))
        if count is not None:
            return count, "luma"

    # 2. Meetup — prefer the number already captured while scraping.
    for src in meetup:
        count = meetup_going_from_payload(getattr(src, "raw_payload", None))
        if count is not None:
            return count, "meetup"

    # 3. Meetup — GraphQL fallback, only when a token is configured.
    if meetup and settings.meetup_api_key:
        for src in meetup:
            event_id = _meetup_event_id(getattr(src, "external_id", None))
            if not event_id:
                continue
            count = _fetch_meetup_going_via_api(event_id, settings.meetup_api_key)
            if count is not None:
                return count, "meetup"

    return None, None


def attendance_for_event(session, event) -> str:
    """Resolve + persist an attendee count for one event from its source platforms. Returns status.

    Status values:
      ``updated``             — a (new/changed) count was stored.
      ``unchanged``           — same count as before; only the checked-at timestamp was refreshed.
      ``skipped:no_source``   — the event has no Luma/Meetup source (stamped checked, won't retry).
      ``skipped:unavailable`` — a relevant source exists but no number was reachable (e.g. Meetup
                                needs a key); checked-at is left unset so a later run retries.
    """
    from sqlmodel import select

    from ..models import EventSource

    sources = session.exec(
        select(EventSource).where(EventSource.event_id == event.id)
    ).all()

    if not any(is_luma_source(s) or is_meetup_source(s) for s in sources):
        # Genuinely no popularity source — stamp it so default runs do not reconsider the event.
        event.attendance_checked_at = _utcnow()
        session.add(event)
        session.commit()
        return "skipped:no_source"

    count, provider = _resolve_count(sources)
    if count is None:
        # Source exists but the number was not reachable (e.g. Meetup API key missing). Leave
        # checked_at unset so adding a key later lets a re-run pick it up.
        return "skipped:unavailable"

    if event.attendee_count == count and event.attendance_source == provider:
        event.attendance_checked_at = _utcnow()
        session.add(event)
        session.commit()
        return "unchanged"

    event.attendee_count = count
    event.attendance_source = provider
    event.attendance_checked_at = _utcnow()
    session.add(event)
    session.commit()
    return "updated"
