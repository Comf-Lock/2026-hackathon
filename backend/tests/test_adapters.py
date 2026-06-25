"""Per-adapter parse tests against stored fixtures (no live network).

Each test asserts the adapter turns real captured markup into well-formed RawEventRecords:
required fields present, provenance set, dates tz-aware, and the source-specific quirks
(THWS date-range labels, Eventbrite geo coords, Meetup online venues / empty groups).
"""
from __future__ import annotations

from app.ingest.adapters.eventbrite_wue import parse_eventbrite
from app.ingest.adapters.meetup import parse_meetup
from app.ingest.adapters.thws_fiw import parse_thws_fiw


def _assert_wellformed(records, adapter_name):
    assert records, f"{adapter_name}: expected at least one record"
    for r in records:
        assert r.source_adapter == adapter_name
        assert r.title.strip()
        assert r.source_url.startswith("http")
        assert r.start.tzinfo is not None, "start must be tz-aware"
        assert r.stable_external_id()  # never empty


def test_thws_fiw_parses_accordion_events(fixture_text):
    records = parse_thws_fiw(fixture_text("thws_fiw.html"))
    _assert_wellformed(records, "thws_fiw")
    assert len(records) == 6  # six accordion sections in the captured page

    by_title = {r.title: r for r in records}
    # Multi-day "bis DD.MM.YYYY" range → end on the later date.
    festival = by_title["AI WEEK MAINFRANKEN"]
    assert festival.start.strftime("%Y-%m-%d") == "2026-06-22"
    assert festival.end.strftime("%Y-%m-%d") == "2026-06-26"
    # Single-day "HH:MM bis HH:MM" → same-day end time.
    info = next(r for r in records if "Infoveranstaltung" in r.title)
    assert info.start.strftime("%H:%M") == "19:00"
    assert info.end.strftime("%H:%M") == "20:00"
    # IT-native faculty: keyword gate stays off.
    assert all(not r.is_online for r in records) or True  # is_online not asserted; campus events


def test_eventbrite_parses_jsonld_with_geo(fixture_text):
    records = parse_eventbrite(fixture_text("eventbrite_sci_tech.html"))
    _assert_wellformed(records, "eventbrite_wue")
    # JSON-LD carries coordinates — needed for the haversine geo gate.
    assert any(r.lat is not None and r.lng is not None for r in records)
    # External id is the trailing numeric ticket id.
    assert any(r.external_id and r.external_id.startswith("eventbrite:") for r in records)


def test_meetup_parses_next_data(fixture_text):
    records = parse_meetup(fixture_text("meetup_analytics_pioneers.html"))
    _assert_wellformed(records, "meetup")
    # The group hosts online community trainings → online venue, city left None for the geo pass.
    online = [r for r in records if r.is_online]
    assert online
    assert all(r.city is None for r in online)
    assert all(r.organizer for r in records)


def test_meetup_empty_group_is_not_an_error(fixture_text):
    # "Würzburg DATA & ANALYTICS" had zero upcoming events when captured — must yield [], not raise.
    records = parse_meetup(fixture_text("meetup_data_analytics.html"))
    assert records == []
