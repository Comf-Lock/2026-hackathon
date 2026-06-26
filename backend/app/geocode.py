"""Geocoding — resolve free-text locations to lat/lng via Nominatim (OpenStreetMap).

Two users:
- ``geocode(query)`` — a one-off lookup (profile home location).
- ``geocode_events(session)`` — the ingest enrichment step: backfill coordinates for stored events
  that have a place (city/address) but no lat/lng yet, so the map can pin them.

Nominatim's usage policy is respected by construction: an identifying ``User-Agent`` (app + contact)
and at most one request per second (``Geocoder`` throttles between *network* calls). Results are
cached per normalized query string, so a run that sees "Würzburg" ten times hits the network once.
The enrichment step only touches events whose ``lat`` is still NULL, so a re-run does no work and
never duplicates a lookup — and every failure (network down, no hit) is swallowed: the event simply
stays without coordinates, never crashing the run.
"""
from __future__ import annotations

import logging
import re
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

import httpx
from sqlmodel import Session, select

from .config import settings
from .models import Event

logger = logging.getLogger("eventradar.geocode")

Coords = tuple[float, float]
_WS_RE = re.compile(r"\s+")


def normalize_query(text: str) -> str:
    """Cache key for a location string: trimmed, lower-cased, whitespace-collapsed."""
    return _WS_RE.sub(" ", (text or "").strip()).casefold()


class Geocoder:
    """Nominatim client with a per-query cache and a ≥1 req/s throttle. Graceful: never raises.

    ``lookup`` can be injected (tests pass a fake) to avoid any real HTTP; the default performs the
    Nominatim request. ``min_interval_s`` is the minimum gap between *network* lookups — cache hits
    are not throttled. Set it to 0 in tests.
    """

    def __init__(
        self,
        *,
        user_agent: str | None = None,
        url: str | None = None,
        min_interval_s: float | None = None,
        lookup: Callable[[str], Awaitable[Coords | None]] | None = None,
    ) -> None:
        self._user_agent = user_agent or settings.nominatim_user_agent
        self._url = url or settings.nominatim_url
        self._min_interval = (
            settings.nominatim_min_interval_s if min_interval_s is None else min_interval_s
        )
        self._lookup_override = lookup
        self._cache: dict[str, Coords | None] = {}
        self._last_call: float | None = None

    async def geocode(self, query: str) -> Coords | None:
        """Return (lat, lng) for ``query`` or None. Cached; only a cache miss hits the network."""
        key = normalize_query(query)
        if not key:
            return None
        if key in self._cache:
            return self._cache[key]
        await self._throttle()
        result = await self._do_lookup(key)
        self._cache[key] = result
        return result

    async def _throttle(self) -> None:
        if self._min_interval <= 0 or self._last_call is None:
            self._last_call = time.monotonic()
            return
        import asyncio

        wait = self._min_interval - (time.monotonic() - self._last_call)
        if wait > 0:
            await asyncio.sleep(wait)
        self._last_call = time.monotonic()

    async def _do_lookup(self, query: str) -> Coords | None:
        if self._lookup_override is not None:
            try:
                return await self._lookup_override(query)
            except Exception as exc:  # an injected lookup must not break the batch either
                logger.warning("geocode lookup failed for %r: %s", query, exc)
                return None
        return await self._nominatim(query)

    async def _nominatim(self, query: str) -> Coords | None:
        params = {"q": query, "format": "json", "limit": 1}
        headers = {"User-Agent": self._user_agent}
        try:
            async with httpx.AsyncClient(timeout=8) as client:
                resp = await client.get(self._url, params=params, headers=headers)
                resp.raise_for_status()
                data = resp.json()
        except Exception as exc:  # network / HTTP / decode — graceful, no coordinates
            logger.warning("nominatim request failed for %r: %s", query, exc)
            return None
        if not data:
            return None
        try:
            return float(data[0]["lat"]), float(data[0]["lon"])
        except (KeyError, IndexError, TypeError, ValueError):
            return None


async def geocode(query: str) -> Coords | None:
    """One-off geocode of a free-text location (profile home). None on no hit / error."""
    return await Geocoder().geocode(query)


def event_query(event: Event) -> str | None:
    """Build the most specific Nominatim query for an event, or None if it has no usable place.

    Uses address/postal/city (venue alone is too ambiguous to geocode reliably) and biases the
    search to Germany so a bare city name resolves to the right country.
    """
    parts = [p for p in (event.address, event.postal_code, event.city) if p]
    if not parts:
        return None
    return ", ".join([*parts, "Deutschland"])


@dataclass
class GeocodeReport:
    scanned: int = 0       # events missing coordinates that were considered
    geocoded: int = 0      # events that got lat/lng this run
    no_query: int = 0      # skipped — no city/address to search on
    no_hit: int = 0        # had a query but Nominatim returned nothing


async def geocode_events(
    session: Session,
    geocoder: Geocoder | None = None,
    *,
    limit: int | None = None,
) -> GeocodeReport:
    """Backfill lat/lng for stored events that have a place but no coordinates. Idempotent.

    Only events with ``lat IS NULL`` and not online are touched, so a re-run is a near-no-op and the
    per-query cache means a repeated city is looked up once. Failures leave the event unchanged.
    """
    geocoder = geocoder or Geocoder()
    report = GeocodeReport()

    stmt = select(Event).where(Event.lat == None, Event.is_online == False)  # noqa: E711
    if limit is not None:
        stmt = stmt.limit(limit)
    events = session.exec(stmt).all()

    for event in events:
        report.scanned += 1
        query = event_query(event)
        if query is None:
            report.no_query += 1
            continue
        coords = await geocoder.geocode(query)
        if coords is None:
            report.no_hit += 1
            continue
        event.lat, event.lng = coords
        session.add(event)
        report.geocoded += 1

    session.commit()
    logger.info(
        "geocode: scanned=%d geocoded=%d no_hit=%d no_query=%d",
        report.scanned, report.geocoded, report.no_hit, report.no_query,
    )
    return report
