"""Adapter: AI Week Mainfranken — the festival's per-session program (ai-week.de).

AI Week is an annual Würzburg AI festival (~40 talks/workshops/hackathon). Its single events live
*only* in a JS-SPA (``programm.php#/veranstaltung/{id}``); every other source (incl. our ZDI-genICS)
carries just the umbrella entry, so without this adapter the single events are missing. There is no
ICS/RSS, hence no feeds.yaml path — it must be a code adapter.

Data path (preferred, no auth): the SPA renders from a single static JSON export that its own bundle
fetches unauthenticated — ``GET https://backend.timetable.ai-week.de/export/session.json`` returns
``{format, sessions[], channels[]}`` for the *current* edition. So the adapter just pulls that export
and maps ``sessions[]`` → RawEventRecord; it is edition-agnostic (next edition ⇒ same URL, new
sessions) and the core's ``end >= today`` filter drops the past ones. The brief's alternative
(optimale-praesentation API with AuthorizationUsername/AuthorizationKey headers) is the upstream
provider; the live site no longer needs it, so we avoid the auth dance and a Playwright render
entirely. The export carries venue + lat/lng inline, so no geocoding is needed either.

``broad = False``: an AI festival is IT-native by construction — many genuine titles ("Fake-Rechnungen
entlarven") carry no keyword, so the core keyword gate must not run. Cancelled sessions are skipped.
"""
from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import Any

from ..registry import register
from ..types import GeoScope, RawEventRecord
from . import _http
from ._normalize import from_iso

logger = logging.getLogger("eventradar.ingest.aiweek")

# Unauthenticated static export the SPA itself fetches (see module docstring).
EXPORT_URL = "https://backend.timetable.ai-week.de/export/session.json"
# Public detail page (hash route) for one session — the human-facing event link.
DETAIL_URL = "https://www.ai-week.de/programm.php#/veranstaltung/{id}"


def _detail_url(session_id: Any) -> str:
    return DETAIL_URL.format(id=session_id)


def _description(session: dict) -> str | None:
    """Prefer the short teaser, fall back to the long text; None when neither is present."""
    desc = session.get("description") or {}
    if not isinstance(desc, dict):
        return None
    text = (desc.get("short") or desc.get("long") or "").strip()
    return text or None


def _event_url(session: dict, fallback: str) -> str:
    """The event's own link if it is a real URL; else the festival detail page.

    ``links.event`` is sometimes an e-mail (``info@host.de``) rather than a URL — only use it when it
    looks like an http(s) link, otherwise keep the canonical detail page.
    """
    link = (session.get("links") or {}).get("event")
    if isinstance(link, str) and link.startswith(("http://", "https://")):
        return link
    return fallback


def _session_to_record(session: dict) -> RawEventRecord | None:
    """Map one export session onto a RawEventRecord. Returns None for unusable/cancelled sessions."""
    if session.get("cancelled"):
        return None

    title = (session.get("title") or "").strip()
    start_raw = session.get("start")
    sid = session.get("id")
    if not title or not start_raw or sid is None:
        return None

    detail = _detail_url(sid)
    loc = session.get("location") or {}
    host = session.get("host") or {}
    channel = session.get("channel") or {}
    tags = [channel["name"]] if channel.get("name") else []

    return RawEventRecord(
        source_adapter="aiweek",
        external_id=f"aiweek:{sid}",
        source_url=detail,
        origin_type="scrape",
        trust_tier=2,  # curated official festival program
        raw_payload=session,
        title=title,
        description=_description(session),
        start=from_iso(start_raw),
        end=from_iso(session["end"]) if session.get("end") else None,
        is_online=bool(session.get("onlineOnly")),
        venue_name=(loc.get("name") or None),
        address=(loc.get("streetNo") or None),
        city=(loc.get("city") or None),
        postal_code=(str(loc["zipcode"]) if loc.get("zipcode") else None),
        lat=loc.get("lat"),
        lng=loc.get("lng"),
        organizer=(host.get("name") or None),
        tags=tags,
        url=_event_url(session, detail),
    )


def parse_sessions(payload: dict) -> list[RawEventRecord]:
    """Pure parse: the export JSON → RawEventRecord list. No network.

    Tolerant of the wrapper shape: a malformed/empty ``sessions`` yields an empty list (a future or
    not-yet-published edition is 0 events, not a crash). Individual unusable sessions are skipped.
    """
    sessions = payload.get("sessions") if isinstance(payload, dict) else None
    if not isinstance(sessions, list):
        return []
    records: list[RawEventRecord] = []
    for session in sessions:
        if not isinstance(session, dict):
            continue
        rec = _session_to_record(session)
        if rec is not None:
            records.append(rec)
    return records


class AiWeekAdapter:
    name = "aiweek"
    broad = False  # AI festival — IT-native by construction; skip the keyword gate.

    async def fetch(self, scope: GeoScope) -> Sequence[RawEventRecord]:
        import json

        raw = await _http.fetch_text(EXPORT_URL)
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            logger.warning("aiweek export is not valid JSON: %s", exc)
            return []
        return parse_sessions(payload)


register(AiWeekAdapter())
