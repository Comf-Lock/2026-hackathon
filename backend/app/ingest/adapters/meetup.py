"""Adapter: Meetup — active Würzburg data/analytics groups.

Sources #7/#8. Meetup is a Next.js SPA, but the initial HTML ships the full event data in the
`__NEXT_DATA__` JSON (an Apollo cache), so we parse JSON-in-HTML instead of driving a browser.
Events live under props.pageProps.__APOLLO_STATE__ as `Event:<id>` objects with `__ref` pointers
to their venue/group. IT-native communities → `broad = False`. The group list is configurable;
Cloudflare is bot-shy, so the real fetch runs at low frequency with a realistic UA.
"""
from __future__ import annotations

import json
import re
from collections.abc import Sequence

from ..registry import register
from ..types import GeoScope, RawEventRecord
from . import _http
from ._dates import from_iso

# Configurable: each entry is a Meetup group's events page (catalogue #7/#8; extend in slice 5).
GROUP_URLS = (
    "https://www.meetup.com/wurzburg-data-analytics-meetup/events/",
    "https://www.meetup.com/analytics-pioneers-wurzburg/events/",
)

_NEXT_RE = re.compile(
    r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', re.S
)
_SKIP_STATUS = {"CANCELLED"}


def _resolve(state: dict, value):
    """Follow an Apollo `{__ref: 'Type:id'}` pointer into the cache; pass through plain dicts."""
    if isinstance(value, dict) and "__ref" in value:
        return state.get(value["__ref"]) or {}
    return value or {}


def _event_to_record(state: dict, ev: dict) -> RawEventRecord | None:
    title = (ev.get("title") or "").strip()
    when = ev.get("dateTime")
    url = ev.get("eventUrl")
    if not title or not when or not url:
        return None
    if (ev.get("status") or "").upper() in _SKIP_STATUS:
        return None

    venue = _resolve(state, ev.get("venue"))
    group = _resolve(state, ev.get("group"))
    is_online = bool(ev.get("isOnline")) or (ev.get("eventType") or "").upper() == "ONLINE"

    return RawEventRecord(
        source_adapter="meetup",
        external_id=f"meetup:{ev.get('id')}",
        source_url=url,
        origin_type="scrape",
        trust_tier=3,  # open community source
        title=title,
        description=(ev.get("description") or None),
        start=from_iso(when),
        end=from_iso(ev["endTime"]) if ev.get("endTime") else None,
        is_online=is_online,
        venue_name=(venue.get("name") or None),
        address=(venue.get("address") or None),
        # Online venues carry an empty city; leave it None so the geo gate uses the online pass.
        city=(venue.get("city") or None) if not is_online else None,
        organizer=(group.get("name") or None),
        url=url,
        language="de",
    )


def parse_meetup(html: str) -> list[RawEventRecord]:
    """Pure parse: a Meetup group page's __NEXT_DATA__ → its RawEventRecord list. No network."""
    m = _NEXT_RE.search(html)
    if not m:
        return []
    try:
        data = json.loads(m.group(1))
    except json.JSONDecodeError:
        return []
    state = data.get("props", {}).get("pageProps", {}).get("__APOLLO_STATE__", {})

    records: list[RawEventRecord] = []
    for key, node in state.items():
        if not key.startswith("Event:") or not isinstance(node, dict):
            continue
        rec = _event_to_record(state, node)
        if rec is not None:
            records.append(rec)
    return records


class MeetupAdapter:
    name = "meetup"
    broad = False  # IT/data communities — no keyword gate

    async def fetch(self, scope: GeoScope) -> Sequence[RawEventRecord]:
        seen: set[str] = set()
        out: list[RawEventRecord] = []
        for url in GROUP_URLS:
            html = await _http.fetch_text(url)
            for rec in parse_meetup(html):
                key = rec.stable_external_id()
                if key not in seen:
                    seen.add(key)
                    out.append(rec)
        return out


register(MeetupAdapter())
