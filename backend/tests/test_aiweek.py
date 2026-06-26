"""AI Week adapter parse tests — pure JSON→records, no network.

Fixture ``aiweek_sessions.json`` is a captured slice of the real export
(https://backend.timetable.ai-week.de/export/session.json, 2026 edition): one online session, one
in-person session with full venue + coordinates, and one cancelled session that must be dropped.
"""
from __future__ import annotations

import json

from app.ingest.adapters.aiweek import parse_sessions
from app.ingest.registry import get_adapters


def _load(fixture_text):
    return parse_sessions(json.loads(fixture_text("aiweek_sessions.json")))


def test_parse_maps_canonical_fields(fixture_text):
    recs = {r.external_id: r for r in _load(fixture_text)}

    # In-person session carries venue, address, city, postal and inline coordinates.
    inperson = recs["aiweek:58"]
    assert inperson.title == "KI-Code: Ship it or get sued?"
    assert inperson.source_adapter == "aiweek"
    assert inperson.origin_type == "scrape"
    assert inperson.is_online is False
    assert inperson.venue_name == "JUN Legal GmbH"
    assert inperson.address == "Salvatorstraße 21"
    assert inperson.city == "Würzburg"
    assert inperson.postal_code == "97074"
    assert inperson.lat == 49.792008686439 and inperson.lng == 9.9539163708687
    assert inperson.organizer == "JUN Legal GmbH"
    assert inperson.tags == ["Tech & Science"]
    # start/end parsed as tz-aware; end present (multi-hour) for the end>=today filter.
    assert inperson.start.isoformat() == "2026-06-22T11:00:00+02:00"
    assert inperson.end.isoformat() == "2026-06-22T12:30:00+02:00"
    # links.event is an e-mail here → url falls back to the festival detail page.
    assert inperson.url == "https://www.ai-week.de/programm.php#/veranstaltung/58"
    assert inperson.source_url == "https://www.ai-week.de/programm.php#/veranstaltung/58"


def test_parse_online_session_uses_event_link(fixture_text):
    recs = {r.external_id: r for r in _load(fixture_text)}

    online = recs["aiweek:66"]
    assert online.is_online is True
    # online session has no location → geo fields stay None (passes geo as "online").
    assert online.city is None and online.lat is None and online.venue_name is None
    # a real http(s) links.event wins over the detail page for the public url.
    assert online.url == "https://gamma.app/docs/Fake-Rechnungen-entlarven-c6dqh1sakjlhg6e"
    assert online.description.startswith("Gefälschte Rechnungen")


def test_cancelled_session_is_dropped(fixture_text):
    recs = _load(fixture_text)
    ids = {r.external_id for r in recs}
    assert "aiweek:101" not in ids  # the cancelled session
    assert len(recs) == 2          # only the two live sessions survive


def test_parse_tolerates_empty_or_malformed():
    assert parse_sessions({}) == []
    assert parse_sessions({"sessions": None}) == []
    assert parse_sessions({"sessions": []}) == []
    assert parse_sessions({"sessions": [{"id": 1}]}) == []  # missing title/start → skipped


def test_adapter_is_registered():
    assert "aiweek" in {a.name for a in get_adapters()}
