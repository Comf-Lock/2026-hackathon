"""End-to-end ingestion smoke against fixtures — registry → fetch → filter → upsert.

`_http.fetch_text` is monkeypatched to serve the stored fixtures by URL, so the real adapters run
with no network. Asserts the cross-cutting guarantees: the geo gate drops out-of-radius events,
the upsert is idempotent across runs, and a failing adapter is isolated (the run still persists the
others).
"""
from __future__ import annotations

import asyncio

import pytest
from sqlmodel import select

from app.ingest import adapters
from app.ingest.adapters import _http, eventbrite_wue, meetup, thws_fiw
from app.ingest.core import run_ingestion
from app.ingest.registry import get_adapters
from app.models import Event, EventSource

# Map every URL the three adapters fetch onto its captured fixture file.
URL_TO_FIXTURE = {
    thws_fiw.PAGE_URL: "thws_fiw.html",
    eventbrite_wue.LISTING_URLS[0]: "eventbrite_sci_tech.html",
    eventbrite_wue.LISTING_URLS[1]: "eventbrite_ki.html",
    meetup.GROUP_URLS[0]: "meetup_data_analytics.html",
    meetup.GROUP_URLS[1]: "meetup_analytics_pioneers.html",
}

# This smoke pins its assertions to the three HTML adapters it has fixtures for. Other registered
# adapters (ICS/RSS sources) fetch URLs that aren't in URL_TO_FIXTURE, so they're excluded here to
# keep the run hermetic and deterministic — they carry their own parse tests.
FIXTURE_ADAPTERS = ["eventbrite_wue", "meetup", "thws_fiw"]


@pytest.fixture
def serve_fixtures(monkeypatch, fixture_text):
    async def fake_fetch(url, *, timeout=None):
        return fixture_text(URL_TO_FIXTURE[url])

    monkeypatch.setattr(_http, "fetch_text", fake_fetch)


def test_three_adapters_register():
    assert {a.name for a in get_adapters()} >= {"thws_fiw", "eventbrite_wue", "meetup"}


def test_full_run_persists_and_filters(serve_fixtures, session):
    report = asyncio.run(run_ingestion(session, names=FIXTURE_ADAPTERS))

    events = session.exec(select(Event)).all()
    assert events, "expected events persisted"

    # Geo gate worked: far-away Eventbrite events (Nürnberg/Heilbronn/Coburg, 80-98km) are dropped,
    # while in-radius Mainfranken towns survive (e.g. Sulzfeld am Main / Miltenberg, < 60km).
    cities = {e.city for e in events if e.city}
    assert cities.isdisjoint({"Nürnberg", "Heilbronn", "Coburg", "Frankfurt am Main", "Hanau"})
    assert cities & {"Sulzfeld am Main", "Miltenberg", "Würzburg"}

    # Every persisted event has provenance from one of our adapters.
    sources = session.exec(select(EventSource)).all()
    assert len(sources) == len(events)
    assert {s.source_adapter for s in sources} <= {"thws_fiw", "eventbrite_wue", "meetup"}

    # For each source: kept <= found (filtering happened, never invented events).
    for r in report.per_source:
        assert r.kept <= r.found
        assert r.error is None


def test_rerun_is_idempotent(serve_fixtures, session):
    first = asyncio.run(run_ingestion(session, names=FIXTURE_ADAPTERS))
    count_after_first = len(session.exec(select(Event)).all())

    second = asyncio.run(run_ingestion(session, names=FIXTURE_ADAPTERS))
    count_after_second = len(session.exec(select(Event)).all())

    assert count_after_second == count_after_first  # no duplicates
    assert second.total_new == 0
    assert second.total_updated == first.total_new  # everything matched and updated in place


def test_failing_adapter_is_isolated(serve_fixtures, session, monkeypatch):
    class BoomAdapter:
        name = "boom"
        broad = False

        async def fetch(self, scope):
            raise RuntimeError("source down")

    from app.ingest import registry

    monkeypatch.setitem(registry._CODE_ADAPTERS, "boom", BoomAdapter())
    report = asyncio.run(run_ingestion(session, names=[*FIXTURE_ADAPTERS, "boom"]))

    boom = next(r for r in report.per_source if r.source == "boom")
    assert boom.error and "source down" in boom.error
    # The healthy adapters still persisted their events despite boom failing.
    assert session.exec(select(Event)).all()
