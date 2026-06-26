"""ICS feed adapters — Meetup group calendars and the ZDI/Gründerzentren genIcs export.

Every Meetup group exposes a working ICS endpoint (``/<slug>/events/ical/``) returning a VCALENDAR;
an empty group yields a valid-but-VEVENT-less calendar, which is normal (it refills before the next
event), never an error. ``ICSFeedAdapter`` fetches one or more such calendar URLs and maps each
VEVENT onto a ``RawEventRecord``.

The ZDI source has no master calendar — only a per-event genIcs export keyed by id — so
``ZdiGenIcsAdapter`` first discovers event ids from the listing page, then pulls each per-event ICS.
It is still ICS parsing, just with a lightweight index step in front; if discovery fails it returns
no records rather than raising (the ingestion core isolates source failures anyway).

``parse_ics`` is a pure text→records function so tests can exercise the mapping without any network.
"""
from __future__ import annotations

import logging
import re
from collections.abc import Sequence

import httpx
from icalendar import Calendar

from .. import http
from ..base import BaseAdapter
from ..registry import register
from ..types import GeoScope, RawEventRecord
from . import _normalize as N

logger = logging.getLogger("eventradar.ingest.ics")

# genIcs links on the Gründerzentren listing carry the event id as `_id=<digits>` alongside the
# `_func=genIcs` marker; the attribute order varies, so match the id on either side of the marker.
_GENICS_ID_RE = re.compile(
    r"_id=(\d+)[^\"'<>]*?genIcs|genIcs[^\"'<>]*?_id=(\d+)", re.IGNORECASE
)


def _str(value: object) -> str | None:
    return str(value) if value is not None else None


def _geo(component: object) -> tuple[float | None, float | None]:
    """Pull lat/lng from a VEVENT GEO property if present, tolerating its varied shapes."""
    raw = component.get("GEO")  # type: ignore[union-attr]
    if raw is None:
        return None, None
    try:
        lat = getattr(raw, "latitude", None)
        lng = getattr(raw, "longitude", None)
        if lat is not None and lng is not None:
            return float(lat), float(lng)
        if isinstance(raw, (tuple, list)) and len(raw) == 2:
            return float(raw[0]), float(raw[1])
    except (TypeError, ValueError):
        pass
    return None, None


def _categories(component: object) -> list[str]:
    raw = component.get("CATEGORIES")  # type: ignore[union-attr]
    if raw is None:
        return []
    cats = getattr(raw, "cats", None)
    if cats:
        return [str(c) for c in cats]
    text = N.clean_text(raw)
    return [t.strip() for t in text.split(",")] if text else []


def _record_from_vevent(
    component: object,
    *,
    source_adapter: str,
    source_url: str,
    origin_type: str,
    trust_tier: int,
    cities: list[str],
    default_city: str | None,
    default_organizer: str | None,
    default_tags: list[str],
) -> RawEventRecord | None:
    """Map a single VEVENT to a RawEventRecord, or None when it lacks a title/start."""
    title = N.clean_text(component.get("SUMMARY"))  # type: ignore[union-attr]
    dtstart = component.get("DTSTART")  # type: ignore[union-attr]
    start = N.to_aware(getattr(dtstart, "dt", None)) if dtstart is not None else None
    if not title or start is None:
        return None

    dtend = component.get("DTEND")  # type: ignore[union-attr]
    end = N.to_aware(getattr(dtend, "dt", None)) if dtend is not None else None

    location = N.clean_text(component.get("LOCATION"))  # type: ignore[union-attr]
    description = N.clean_text(component.get("DESCRIPTION"))  # type: ignore[union-attr]
    uid = _str(component.get("UID"))  # type: ignore[union-attr]
    url = _str(component.get("URL")) or source_url  # type: ignore[union-attr]

    organizer = N.clean_text(component.get("ORGANIZER")) or default_organizer  # type: ignore[union-attr]
    if organizer and organizer.lower().startswith("mailto:"):
        organizer = default_organizer

    lat, lng = _geo(component)
    is_online = N.detect_online(location, description)
    tags = [*default_tags, *_categories(component)]

    venue_name = location.split(",")[0].strip() if location else None

    return RawEventRecord(
        source_adapter=source_adapter,
        external_id=uid,
        source_url=url,
        origin_type=origin_type,
        trust_tier=trust_tier,
        title=title,
        description=description,
        start=start,
        end=end,
        is_online=is_online,
        venue_name=venue_name,
        address=location,
        city=None if is_online else N.pick_city(location, cities, default_city),
        postal_code=N.extract_postal(location),
        lat=lat,
        lng=lng,
        organizer=organizer,
        tags=tags,
        url=url,
        language=_str(component.get("X-LANGUAGE")),  # type: ignore[union-attr]
    )


def parse_ics(
    text: str,
    *,
    source_adapter: str,
    source_url: str,
    origin_type: str = "feed",
    trust_tier: int = 2,
    cities: list[str] | None = None,
    default_city: str | None = None,
    default_organizer: str | None = None,
    default_tags: list[str] | None = None,
) -> list[RawEventRecord]:
    """Parse a VCALENDAR text into RawEventRecords. Bad VEVENTs are skipped, not fatal."""
    cities = cities if cities is not None else GeoScope().cities
    default_tags = default_tags or []
    try:
        cal = Calendar.from_ical(text)
    except (ValueError, IndexError) as exc:
        logger.warning("ICS parse failed for %s: %s", source_adapter, exc)
        return []

    records: list[RawEventRecord] = []
    for component in cal.walk("VEVENT"):
        try:
            record = _record_from_vevent(
                component,
                source_adapter=source_adapter,
                source_url=source_url,
                origin_type=origin_type,
                trust_tier=trust_tier,
                cities=cities,
                default_city=default_city,
                default_organizer=default_organizer,
                default_tags=default_tags,
            )
        except Exception as exc:  # one malformed VEVENT must not drop the rest
            logger.warning("skip VEVENT in %s: %s", source_adapter, exc)
            continue
        if record is not None:
            records.append(record)
    return records


class ICSFeedAdapter(BaseAdapter):
    """Generic adapter over one or more full-calendar ICS URLs."""

    def __init__(
        self,
        name: str,
        urls: Sequence[str],
        *,
        broad: bool = False,
        origin_type: str = "feed",
        trust_tier: int = 2,
        default_city: str | None = None,
        default_organizer: str | None = None,
        default_tags: list[str] | None = None,
    ) -> None:
        self.name = name
        self.urls = list(urls)
        self.broad = broad
        self.origin_type = origin_type
        self.trust_tier = trust_tier
        self.default_city = default_city
        self.default_organizer = default_organizer
        self.default_tags = default_tags or []

    async def fetch(self, scope: GeoScope) -> Sequence[RawEventRecord]:
        records: list[RawEventRecord] = []
        async with http.client() as client:
            for url in self.urls:
                try:
                    resp = await client.get(url)
                    resp.raise_for_status()
                except httpx.HTTPError as exc:
                    logger.warning("ICS fetch failed %s: %s", url, exc)
                    continue
                records.extend(
                    parse_ics(
                        resp.text,
                        source_adapter=self.name,
                        source_url=url,
                        origin_type=self.origin_type,
                        trust_tier=self.trust_tier,
                        cities=scope.cities,
                        default_city=self.default_city,
                        default_organizer=self.default_organizer,
                        default_tags=self.default_tags,
                    )
                )
        return records


def _extract_genics_ids(html: str, *, limit: int = 60) -> list[str]:
    """Extract distinct genIcs event ids from a listing page, preserving first-seen order."""
    seen: list[str] = []
    for left, right in _GENICS_ID_RE.findall(html):
        ev_id = left or right
        if ev_id and ev_id not in seen:
            seen.append(ev_id)
        if len(seen) >= limit:
            break
    return seen


class ZdiGenIcsAdapter(BaseAdapter):
    """ZDI / Gründerzentren Würzburg — discover event ids on the listing, pull per-event genIcs."""

    name = "zdi_gruenderzentren"
    broad = False

    LISTING_URL = (
        "https://www.gruenderzentren-wuerzburg.de/gruenderzentren/veranstaltungen/index.html"
    )
    ICS_TEMPLATE = (
        "https://www.gruenderzentren-wuerzburg.de/gruenderzentren/veranstaltungen/"
        "index.html?_func=genIcs&_eopb=1&_id={id}"
    )

    async def fetch(self, scope: GeoScope) -> Sequence[RawEventRecord]:
        records: list[RawEventRecord] = []
        async with http.client() as client:
            try:
                listing = await client.get(self.LISTING_URL)
                listing.raise_for_status()
            except httpx.HTTPError as exc:
                logger.warning("ZDI listing fetch failed: %s", exc)
                return []

            ids = _extract_genics_ids(listing.text)
            logger.info("ZDI genIcs: %d event ids discovered", len(ids))
            for ev_id in ids:
                url = self.ICS_TEMPLATE.format(id=ev_id)
                try:
                    resp = await client.get(url)
                    resp.raise_for_status()
                except httpx.HTTPError as exc:
                    logger.warning("ZDI genIcs fetch failed id=%s: %s", ev_id, exc)
                    continue
                records.extend(
                    parse_ics(
                        resp.text,
                        source_adapter=self.name,
                        source_url=url,
                        origin_type="feed",
                        trust_tier=1,
                        cities=scope.cities,
                        default_city="Würzburg",
                        default_organizer="Gründerzentren Würzburg",
                        default_tags=["zdi", "gruenderzentrum"],
                    )
                )
        return records


# --- Self-registration (import side-effect via adapters/__init__) ------------------------------
# The generic Meetup ICS feeds moved to feeds.yaml (data-driven, see ingest/feed_loader.py).
# ZdiGenIcsAdapter stays a code adapter: it discovers event ids and pulls a per-event genIcs export,
# which is not a single-URL calendar a config entry could express.
register(ZdiGenIcsAdapter())
