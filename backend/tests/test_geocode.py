"""Geocoding tests — all offline: the Nominatim call is replaced by an injected fake lookup.

Covers the enrichment contract: city → lat/lng, the per-query cache prevents a second lookup,
online/place-less/already-geocoded events are handled correctly, a re-run is idempotent, and every
failure is graceful (no hit / raising lookup → None, never an exception).
"""
from __future__ import annotations

from datetime import datetime, timezone

from app.config import settings
from app.geocode import Geocoder, event_query, geocode_events, normalize_query
from app.models import Event

WUE = (49.7913, 9.9534)


class FakeLookup:
    """Stand-in for the Nominatim network call — records calls, answers from a table."""

    def __init__(self, table: dict[str, tuple[float, float] | None]):
        self.table = table
        self.calls: list[str] = []

    async def __call__(self, query: str):
        self.calls.append(query)
        return self.table.get(query)


def _event(session, **kw) -> Event:
    kw.setdefault("title", "Event")
    kw.setdefault("start", datetime(2099, 1, 1, 18, 0, tzinfo=timezone.utc))
    ev = Event(**kw)
    session.add(ev)
    session.commit()
    session.refresh(ev)
    return ev


# --- Geocoder unit: cache + graceful ------------------------------------------------------------

def test_normalize_query():
    assert normalize_query("  Würzburg   , DE ") == "würzburg , de"


def test_geocoder_caches_lookup():
    import asyncio

    fake = FakeLookup({"würzburg, deutschland": WUE})
    g = Geocoder(lookup=fake, min_interval_s=0)

    a = asyncio.run(g.geocode("Würzburg, Deutschland"))
    b = asyncio.run(g.geocode("würzburg,  deutschland"))  # same after normalization
    assert a == WUE and b == WUE
    assert fake.calls == ["würzburg, deutschland"]  # second call served from cache


def test_geocoder_graceful_on_no_hit_and_error():
    import asyncio

    async def boom(_q):
        raise RuntimeError("network down")

    assert asyncio.run(Geocoder(lookup=boom, min_interval_s=0).geocode("x")) is None

    miss = FakeLookup({})  # query not in table → None
    assert asyncio.run(Geocoder(lookup=miss, min_interval_s=0).geocode("nowhere")) is None


def test_geocoder_uses_policy_user_agent():
    g = Geocoder()
    assert g._user_agent == settings.nominatim_user_agent
    assert "contact" in g._user_agent.lower()  # identifying contact per Nominatim policy
    assert settings.nominatim_min_interval_s >= 1.0  # ≥ 1 req/s


# --- event_query --------------------------------------------------------------------------------

def test_event_query_builds_from_place_fields():
    ev = Event(title="t", start=datetime(2099, 1, 1, tzinfo=timezone.utc),
               address="Sanderring 2", postal_code="97070", city="Würzburg")
    assert event_query(ev) == "Sanderring 2, 97070, Würzburg, Deutschland"
    # No place at all → no query (venue name alone is intentionally not used).
    assert event_query(Event(title="t", start=datetime(2099, 1, 1, tzinfo=timezone.utc),
                             venue_name="Some Hall")) is None


# --- geocode_events integration -----------------------------------------------------------------

def test_geocode_events_sets_coordinates_and_caches(session):
    e1 = _event(session, city="Würzburg")
    e2 = _event(session, city="Würzburg")                       # same city → 1 lookup (cache)
    e_online = _event(session, city=None, is_online=True)       # online → not scanned
    e_noplace = _event(session, city=None, address=None)        # no query
    e_nohit = _event(session, city="Nirgendwo")                 # lookup returns None
    e_done = _event(session, city="Würzburg", lat=1.0, lng=2.0)  # already geocoded → skipped

    fake = FakeLookup({"würzburg, deutschland": WUE})            # "nirgendwo, ..." absent → None
    report = geocode_events_sync(session, Geocoder(lookup=fake, min_interval_s=0))

    session.refresh(e1); session.refresh(e2); session.refresh(e_done)
    assert (e1.lat, e1.lng) == WUE
    assert (e2.lat, e2.lng) == WUE
    assert (e_done.lat, e_done.lng) == (1.0, 2.0)               # untouched (idempotent)
    assert fake.calls.count("würzburg, deutschland") == 1      # e1+e2 share one lookup (cache)
    assert fake.calls.count("nirgendwo, deutschland") == 1     # the no-hit query is tried once

    assert report.scanned == 4                                  # e1,e2,e_noplace,e_nohit
    assert report.geocoded == 2
    assert report.no_query == 1
    assert report.no_hit == 1
    # e_online never selected
    session.refresh(e_online)
    assert e_online.lat is None


def test_geocode_events_rerun_is_idempotent(session):
    _event(session, city="Würzburg")
    fake = FakeLookup({"würzburg, deutschland": WUE})
    g = Geocoder(lookup=fake, min_interval_s=0)

    first = geocode_events_sync(session, g)
    assert first.geocoded == 1

    # Second run: the geocoded event now has coords → excluded, nothing to do.
    second = geocode_events_sync(session, Geocoder(lookup=fake, min_interval_s=0))
    assert second.scanned == 0
    assert second.geocoded == 0


def geocode_events_sync(session, geocoder):
    import asyncio

    return asyncio.run(geocode_events(session, geocoder))
