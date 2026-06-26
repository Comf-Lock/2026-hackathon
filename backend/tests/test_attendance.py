"""Tests for the attendance / RSVP popularity step.

The only network boundaries — ``attendance._fetch_url`` (Luma) and
``attendance._fetch_meetup_going_via_api`` (Meetup GraphQL) — are always mocked here: the suite
never makes a real call. The pure extractors and the orchestration/persistence are exercised for
real against an in-memory DB.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.enrichment import attendance
from app.models import Event, EventSource

NOW = datetime.now(timezone.utc)

# A minimal Luma event page: the count lives in the embedded __NEXT_DATA__ JSON.
LUMA_HTML = (
    '<html><head></head><body>'
    '<script id="__NEXT_DATA__" type="application/json">'
    '{"props":{"pageProps":{"event":{"name":"AI Night","guest_count":137,'
    '"approved_guest_count":120}}}}'
    '</script></body></html>'
)


def _event(session, **kw) -> Event:
    defaults = dict(title="Event", start=NOW + timedelta(days=1), is_online=False, tags=[])
    defaults.update(kw)
    ev = Event(**defaults)
    session.add(ev)
    session.commit()
    session.refresh(ev)
    return ev


def _source(session, event, **kw) -> EventSource:
    defaults = dict(
        event_id=event.id,
        source_adapter="meetup",
        external_id="meetup:315082274",
        source_url="https://www.meetup.com/x/events/315082274/",
        raw_payload={},
    )
    defaults.update(kw)
    src = EventSource(**defaults)
    session.add(src)
    session.commit()
    return src


# --- pure extractors -----------------------------------------------------------------------


def test_meetup_going_from_payload():
    assert attendance.meetup_going_from_payload({"going_count": 42}) == 42
    assert attendance.meetup_going_from_payload({"going_count": 0}) == 0
    assert attendance.meetup_going_from_payload({}) is None
    assert attendance.meetup_going_from_payload({"going_count": -1}) is None
    assert attendance.meetup_going_from_payload(None) is None
    assert attendance.meetup_going_from_payload("nope") is None


def test_parse_luma_guest_count_from_next_data():
    assert attendance.parse_luma_guest_count(LUMA_HTML) == 137


def test_parse_luma_guest_count_regex_fallback():
    # No __NEXT_DATA__ wrapper — the raw-regex fallback still finds it.
    assert attendance.parse_luma_guest_count('...{"guest_count": 88}...') == 88


def test_parse_luma_guest_count_none_when_absent():
    assert attendance.parse_luma_guest_count("<html>no count here</html>") is None
    assert attendance.parse_luma_guest_count("") is None
    assert attendance.parse_luma_guest_count(None) is None


def test_source_classification():
    meetup = EventSource(event_id=1, source_adapter="meetup", external_id="m:1",
                         source_url="https://www.meetup.com/g/events/1/")
    luma = EventSource(event_id=1, source_adapter="feed", external_id="l:1",
                       source_url="https://lu.ma/abc123")
    other = EventSource(event_id=1, source_adapter="thws_fiw", external_id="t:1",
                        source_url="https://thws.de/x")
    assert attendance.is_meetup_source(meetup) and not attendance.is_luma_source(meetup)
    assert attendance.is_luma_source(luma) and not attendance.is_meetup_source(luma)
    assert not attendance.is_meetup_source(other) and not attendance.is_luma_source(other)


# --- orchestration (network mocked) --------------------------------------------------------


def test_meetup_count_from_scraped_payload_no_key(session, monkeypatch):
    # No API key, no Luma — the count comes straight from the scraped raw_payload.
    monkeypatch.setattr(attendance.settings, "meetup_api_key", "")
    boom = lambda *a, **k: pytest.fail("must not hit the network")  # noqa: E731
    monkeypatch.setattr(attendance, "_fetch_url", boom)
    monkeypatch.setattr(attendance, "_fetch_meetup_going_via_api", boom)

    ev = _event(session)
    _source(session, ev, raw_payload={"going_count": 23})

    assert attendance.attendance_for_event(session, ev) == "updated"
    session.refresh(ev)
    assert ev.attendee_count == 23
    assert ev.attendance_source == "meetup"
    assert ev.attendance_checked_at is not None


def test_luma_preferred_over_meetup(session, monkeypatch):
    monkeypatch.setattr(attendance, "_fetch_url", lambda url: LUMA_HTML)
    ev = _event(session)
    _source(session, ev, source_adapter="feed", external_id="l:1",
            source_url="https://lu.ma/ai-night")
    _source(session, ev, source_adapter="meetup", external_id="m:1",
            source_url="https://www.meetup.com/g/events/1/", raw_payload={"going_count": 5})

    assert attendance.attendance_for_event(session, ev) == "updated"
    session.refresh(ev)
    assert ev.attendee_count == 137
    assert ev.attendance_source == "luma"


def test_meetup_api_fallback_only_with_key(session, monkeypatch):
    # Meetup source, no scraped count, no key → unavailable, nothing persisted, retryable.
    monkeypatch.setattr(attendance.settings, "meetup_api_key", "")
    monkeypatch.setattr(attendance, "_fetch_meetup_going_via_api",
                        lambda *a, **k: pytest.fail("API must not be called without a key"))
    ev = _event(session)
    _source(session, ev, raw_payload={})

    assert attendance.attendance_for_event(session, ev) == "skipped:unavailable"
    session.refresh(ev)
    assert ev.attendee_count is None
    assert ev.attendance_checked_at is None  # left unset so a later run with a key retries

    # Now with a key the GraphQL fallback supplies the number.
    monkeypatch.setattr(attendance.settings, "meetup_api_key", "tok")
    monkeypatch.setattr(attendance, "_fetch_meetup_going_via_api", lambda eid, token: 64)
    assert attendance.attendance_for_event(session, ev) == "updated"
    session.refresh(ev)
    assert ev.attendee_count == 64
    assert ev.attendance_source == "meetup"


def test_no_relevant_source_is_stamped_and_skipped(session, monkeypatch):
    ev = _event(session)
    _source(session, ev, source_adapter="thws_fiw", external_id="t:1",
            source_url="https://thws.de/x")
    assert attendance.attendance_for_event(session, ev) == "skipped:no_source"
    session.refresh(ev)
    assert ev.attendee_count is None
    assert ev.attendance_checked_at is not None  # stamped → default runs won't reconsider it


def test_unchanged_count_reports_unchanged(session, monkeypatch):
    monkeypatch.setattr(attendance.settings, "meetup_api_key", "")
    ev = _event(session)
    _source(session, ev, raw_payload={"going_count": 12})

    assert attendance.attendance_for_event(session, ev) == "updated"
    session.refresh(ev)
    first_checked = ev.attendance_checked_at
    assert attendance.attendance_for_event(session, ev) == "unchanged"
    session.refresh(ev)
    assert ev.attendee_count == 12
    assert ev.attendance_checked_at >= first_checked


def test_meetup_event_id_extraction():
    assert attendance._meetup_event_id("meetup:315082274") == "315082274"
    assert attendance._meetup_event_id("315082274") == "315082274"
    assert attendance._meetup_event_id(None) is None
    assert attendance._meetup_event_id("") is None
