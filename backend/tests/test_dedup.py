"""Cross-source dedup (slice 5 v1): fingerprint purity + the upsert merge/idempotency contract.

Unit half pins the pure fingerprint: cross-source title/case/accent variants of the *same* event
collapse to one key, while a different day splits them. Integration half drives upsert_event over
an in-memory DB and asserts the headline guarantee — the same event from two sources becomes one
Event with two EventSource rows, and a re-run changes nothing.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlmodel import select

from app.ingest.core import upsert_event
from app.ingest.dedup import (
    event_fingerprint,
    normalize_location,
    normalize_title,
    record_fingerprint,
)
from app.ingest.types import RawEventRecord
from app.models import Event, EventSource

START = datetime(2026, 7, 15, 18, 30, tzinfo=timezone.utc)


def _record(source_adapter: str, external_id: str, *, title="KI Meetup Würzburg",
            start=START, city="Würzburg", is_online=False, **extra) -> RawEventRecord:
    return RawEventRecord(
        source_adapter=source_adapter,
        external_id=external_id,
        source_url=f"https://{source_adapter}.example/{external_id}",
        title=title,
        start=start,
        city=city,
        is_online=is_online,
        **extra,
    )


# --- Unit: normalization + fingerprint -------------------------------------------------

def test_normalize_title_folds_case_accents_and_filler():
    assert normalize_title("Die KI-Konferenz Würzburg") == "ki konferenz wurzburg"
    assert normalize_title("KI Konferenz Wurzburg") == "ki konferenz wurzburg"


def test_normalize_location_online_vs_city():
    assert normalize_location("Würzburg", is_online=False) == "wurzburg"
    assert normalize_location("Würzburg", is_online=True) == "online"
    assert normalize_location(None, is_online=False) == ""


def test_same_event_cross_source_shares_fingerprint():
    # Same event, different surface form on two sources → identical fingerprint.
    a = event_fingerprint("Die KI-Konferenz Würzburg", START, "Würzburg", False)
    b = event_fingerprint("KI Konferenz Wurzburg", START, "würzburg", False)
    assert a == b


def test_different_day_splits_fingerprint():
    other_day = START.replace(day=16)
    assert event_fingerprint("KI Meetup", START, "Würzburg", False) != event_fingerprint(
        "KI Meetup", other_day, "Würzburg", False
    )


# --- Integration: upsert merge + idempotency ------------------------------------------

def test_two_sources_same_event_merge_to_one_event(session):
    created_a = upsert_event(session, _record("meetup", "m-1"))
    created_b = upsert_event(session, _record("eventbrite_wue", "e-9"))
    session.commit()

    assert created_a is True   # first source creates the Event
    assert created_b is False  # second source merges into it, no new Event

    events = session.exec(select(Event)).all()
    sources = session.exec(select(EventSource)).all()
    assert len(events) == 1
    assert len(sources) == 2
    assert {s.source_adapter for s in sources} == {"meetup", "eventbrite_wue"}
    assert all(s.event_id == events[0].id for s in sources)


def test_merge_is_idempotent_on_rerun(session):
    for rec in (_record("meetup", "m-1"), _record("eventbrite_wue", "e-9")):
        upsert_event(session, rec)
    session.commit()

    # Re-run both records: nothing new, counts unchanged.
    for rec in (_record("meetup", "m-1"), _record("eventbrite_wue", "e-9")):
        assert upsert_event(session, rec) is False
    session.commit()

    assert len(session.exec(select(Event)).all()) == 1
    assert len(session.exec(select(EventSource)).all()) == 2


def test_different_event_stays_separate(session):
    upsert_event(session, _record("meetup", "m-1", start=START))
    # Same title/city but a different day → a distinct event, must not merge.
    upsert_event(session, _record("eventbrite_wue", "e-9", start=START.replace(day=16)))
    session.commit()

    assert len(session.exec(select(Event)).all()) == 2


def test_merge_backfills_missing_fields_without_clobbering(session):
    upsert_event(session, _record("meetup", "m-1", image_url=None, organizer="Meetup Group"))
    upsert_event(session, _record("eventbrite_wue", "e-9", image_url="https://img/x.jpg",
                                  organizer="Other Org"))
    session.commit()

    event = session.exec(select(Event)).one()
    assert event.image_url == "https://img/x.jpg"   # backfilled (was empty)
    assert event.organizer == "Meetup Group"         # kept — first source stays canonical
