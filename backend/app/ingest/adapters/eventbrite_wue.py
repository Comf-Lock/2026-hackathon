"""Adapter: Eventbrite — Würzburg "Science & Tech" + "Künstliche Intelligenz" listings.

Sources #5/#6. The listing pages are server-rendered and embed a JSON-LD `ItemList` of
schema.org `Event` objects — far more robust than scraping the visual cards, and it carries
geo coordinates, so the core's haversine gate can filter precisely. Eventbrite's topic search is
loose (it pads the "KI"/"science-and-tech" lists with popular local non-IT events), so this is a
`broad` source — the core keyword gate weeds those out. We crawl the two listing URLs once per run
(low frequency, realistic UA); deeper pagination is deferred — page 1 already yields the upcoming.
"""
from __future__ import annotations

import json
import re
from collections.abc import Sequence

from ..registry import register
from ..types import GeoScope, RawEventRecord
from . import _http
from ._dates import from_iso, from_iso_date

LISTING_URLS = (
    "https://www.eventbrite.com/b/germany--w%C3%BCrzburg/science-and-tech/",
    "https://www.eventbrite.de/d/germany--w%C3%BCrzburg/k%C3%BCnstliche-intelligenz/",
)

_LD_RE = re.compile(r'<script type="application/ld\+json">(.*?)</script>', re.S)
_ID_RE = re.compile(r"(\d+)/?$")  # trailing numeric id in ".../...-tickets-1404642727209"


def _to_float(value) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _price(ev: dict) -> str | None:
    """Map schema.org offers to a short price string. A free event has lowPrice 0 (falsy), so we
    must check for None explicitly — `lowPrice or price` would swallow it and miss "kostenlos"."""
    offers = ev.get("offers")
    if isinstance(offers, list):
        offers = next((o for o in offers if isinstance(o, dict)), None)
    if not isinstance(offers, dict):
        return None
    low = offers.get("lowPrice")
    if low is None:
        low = offers.get("price")
    if low in (0, "0", "0.0"):
        return "kostenlos"
    if low:
        return f"ab {low} {offers.get('priceCurrency', '')}".strip()
    return None


def _parse_date(value: str | None):
    """Eventbrite gives either a bare date ('2026-06-26') or a full ISO datetime."""
    if not value:
        return None
    return from_iso(value) if "T" in value else from_iso_date(value)


def _event_to_record(ev: dict) -> RawEventRecord | None:
    title = (ev.get("name") or "").strip()
    start = _parse_date(ev.get("startDate"))
    url = ev.get("url")
    if not title or start is None or not url:
        return None

    loc = ev.get("location") or {}
    addr = loc.get("address") or {}
    geo = loc.get("geo") or {}
    mode = (ev.get("eventAttendanceMode") or "").lower()

    id_match = _ID_RE.search(url)
    external_id = f"eventbrite:{id_match.group(1)}" if id_match else None

    return RawEventRecord(
        source_adapter="eventbrite_wue",
        external_id=external_id,
        source_url=url,
        origin_type="scrape",
        trust_tier=2,  # open aggregator
        raw_payload=ev,
        title=title,
        description=(ev.get("description") or None),
        start=start,
        end=_parse_date(ev.get("endDate")),
        is_online="online" in mode and "offline" not in mode,
        venue_name=(loc.get("name") or None),
        address=(addr.get("streetAddress") or None),
        city=(addr.get("addressLocality") or None),
        postal_code=(addr.get("postalCode") or None),
        lat=_to_float(geo.get("latitude")),
        lng=_to_float(geo.get("longitude")),
        url=url,
        image_url=(ev.get("image") or None),
        price=_price(ev),
    )


def _iter_events(node):
    """Yield every schema.org Event dict nested in a JSON-LD node (ItemList → item, or bare)."""
    if isinstance(node, list):
        for x in node:
            yield from _iter_events(x)
    elif isinstance(node, dict):
        if node.get("@type") == "Event":
            yield node
        if "item" in node:
            yield from _iter_events(node["item"])
        if "itemListElement" in node:
            yield from _iter_events(node["itemListElement"])


def parse_eventbrite(html: str) -> list[RawEventRecord]:
    """Pure parse: page HTML → RawEventRecord list from its JSON-LD blocks. No network."""
    records: list[RawEventRecord] = []
    for block in _LD_RE.findall(html):
        try:
            data = json.loads(block)
        except json.JSONDecodeError:
            continue
        for ev in _iter_events(data):
            rec = _event_to_record(ev)
            if rec is not None:
                records.append(rec)
    return records


class EventbriteWueAdapter:
    name = "eventbrite_wue"
    # broad=True: Eventbrite's topic search is loose — the "KI"/"science-and-tech" listings are
    # padded with popular *local* non-IT events (bike repair, grill nights, raves). So the core
    # keyword gate must run on the title/tags to keep only the genuinely IT-relevant ones.
    broad = True

    async def fetch(self, scope: GeoScope) -> Sequence[RawEventRecord]:
        seen: set[str] = set()
        out: list[RawEventRecord] = []
        for url in LISTING_URLS:
            html = await _http.fetch_text(url)
            for rec in parse_eventbrite(html):
                key = rec.stable_external_id()
                if key not in seen:  # the two listings overlap — dedup within the run
                    seen.add(key)
                    out.append(rec)
        return out


register(EventbriteWueAdapter())
