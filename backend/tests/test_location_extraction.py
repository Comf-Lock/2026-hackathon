"""Location-extraction tests — adapters must mine venue/city/postal/coords from the source data.

Pure parse, no network: feeds the adapters real/synthetic source payloads and asserts the
RawEventRecord carries the location fields the map needs. The geocode step (test_geocode.py) then
only fills what is genuinely absent.
"""
from __future__ import annotations

import json
import pathlib

from app.ingest.adapters.eventbrite_wue import parse_eventbrite
from app.ingest.adapters.meetup import parse_meetup
from app.ingest.adapters.rss import parse_rss
from app.ingest.adapters.thws_fiw import parse_thws_fiw

from test_adapters import RSS_SAMPLE

FIXTURES = pathlib.Path(__file__).parent / "fixtures"


# --- Meetup: venue + group-fallback coordinates -------------------------------------------------

def _meetup_html(state: dict) -> str:
    payload = {"props": {"pageProps": {"__APOLLO_STATE__": state}}}
    return (
        '<script id="__NEXT_DATA__" type="application/json">'
        + json.dumps(payload)
        + "</script>"
    )


def test_meetup_extracts_venue_coordinates():
    state = {
        "Event:1": {
            "__typename": "Event", "id": "1", "title": "In-Person ML Talk",
            "dateTime": "2026-09-01T18:00:00+02:00", "eventUrl": "https://www.meetup.com/g/events/1/",
            "isOnline": False, "venue": {"__ref": "Venue:1"}, "group": {"__ref": "Group:1"},
        },
        "Venue:1": {
            "__typename": "Venue", "name": "ZDI Cube", "address": "Veitshöchheimer Str. 5",
            "city": "Würzburg", "postalCode": "97080", "lat": 49.7913, "lng": 9.9534,
        },
        "Group:1": {"__typename": "Group", "name": "WUE ML", "lat": 49.8, "lon": 9.94, "city": "Würzburg"},
    }
    [rec] = parse_meetup(_meetup_html(state))
    assert rec.venue_name == "ZDI Cube"
    assert rec.city == "Würzburg"
    assert rec.postal_code == "97080"
    assert (rec.lat, rec.lng) == (49.7913, 9.9534)  # venue coords win


def test_meetup_falls_back_to_group_location():
    state = {
        "Event:2": {
            "__typename": "Event", "id": "2", "title": "Community Night",
            "dateTime": "2026-09-02T18:00:00+02:00", "eventUrl": "https://www.meetup.com/g/events/2/",
            "isOnline": False, "venue": {"__ref": "Venue:2"}, "group": {"__ref": "Group:1"},
        },
        # Sparse venue (no city, no coords) — the group supplies the fallback location.
        "Venue:2": {"__typename": "Venue", "name": "TBA", "address": "", "city": "", "lat": None, "lng": None},
        "Group:1": {"__typename": "Group", "name": "WUE ML", "lat": 49.8, "lon": 9.94, "city": "Würzburg"},
    }
    [rec] = parse_meetup(_meetup_html(state))
    assert rec.city == "Würzburg"
    assert (rec.lat, rec.lng) == (49.8, 9.94)  # group lon → lng


def test_meetup_online_event_has_no_location():
    state = {
        "Event:3": {
            "__typename": "Event", "id": "3", "title": "Online Webinar",
            "dateTime": "2026-09-03T18:00:00+02:00", "eventUrl": "https://www.meetup.com/g/events/3/",
            "isOnline": True, "venue": {"__ref": "Venue:1"}, "group": {"__ref": "Group:1"},
        },
        "Venue:1": {"__typename": "Venue", "name": "ZDI Cube", "city": "Würzburg", "lat": 49.79, "lng": 9.95},
        "Group:1": {"__typename": "Group", "name": "WUE ML", "lat": 49.8, "lon": 9.94, "city": "Würzburg"},
    }
    [rec] = parse_meetup(_meetup_html(state))
    assert rec.is_online is True
    assert rec.city is None
    assert rec.lat is None and rec.lng is None


# --- THWS-FIW: Würzburg faculty default, Schweinfurt override -----------------------------------

def test_thws_fiw_defaults_city_to_wuerzburg():
    records = parse_thws_fiw((FIXTURES / "thws_fiw.html").read_text(encoding="utf-8"))
    assert records
    # FIW is a Würzburg faculty → every event now carries a city (0 → all, the map win).
    assert all(r.city == "Würzburg" for r in records)


def test_thws_fiw_overrides_to_schweinfurt_when_named():
    html = (
        '<a data-toggle="collapse" aria-label="01.10.2026 : Infotag am Campus Schweinfurt" '
        'href="#c1"><div class="row"></div></a>'
    )
    [rec] = parse_thws_fiw(html)
    assert rec.city == "Schweinfurt"


# --- Eventbrite: derive city/postal from a street-only address ----------------------------------

def test_eventbrite_derives_city_postal_from_street():
    html = (
        '<script type="application/ld+json">'
        '{"@type":"Event","name":"KI Workshop","startDate":"2026-09-01T18:00",'
        '"url":"https://www.eventbrite.com/e/ki-workshop-tickets-555",'
        '"location":{"@type":"Place","name":"Hörsaal","address":{"@type":"PostalAddress",'
        '"streetAddress":"Sanderring 2, 97070 Würzburg"}}}'
        "</script>"
    )
    [rec] = parse_eventbrite(html)
    assert rec.city == "Würzburg"   # mined from the free-text street
    assert rec.postal_code == "97070"


# --- RSS (FRIZZ): venue from the "@ <venue>" title tail -----------------------------------------

def test_rss_extracts_venue_from_title():
    recs = parse_rss(
        RSS_SAMPLE,
        source_adapter="frizz_wuerzburg",
        source_url="https://frizz-wuerzburg.de/rss",
        default_city="Würzburg",
        prefer_title_date=True,
    )
    hack = next(r for r in recs if r.external_id == "frizz-123")
    assert hack.venue_name == "ZDI Cube"   # from "... @ ZDI Cube"
    assert hack.city == "Würzburg"
