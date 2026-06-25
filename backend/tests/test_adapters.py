"""Adapter parse tests — pure text→records, no network."""
from __future__ import annotations

from app.ingest.adapters._normalize import parse_de_datetime
from app.ingest.adapters.ics import _extract_genics_ids, parse_ics
from app.ingest.adapters.rss import parse_rss

ICS_SAMPLE = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Meetup//EN
BEGIN:VEVENT
UID:event-12345@meetup.com
SUMMARY:AI Week: Python for Machine Learning
DTSTART:20260710T180000Z
DTEND:20260710T200000Z
LOCATION:ZDI Cube, Veitshöchheimer Str. 5, 97080 Würzburg, Germany
DESCRIPTION:Hands-on workshop. Bring a laptop.
URL:https://www.meetup.com/wurzburg-data-analytics-meetup/events/12345/
CATEGORIES:Workshop,AI
GEO:49.79;9.95
END:VEVENT
BEGIN:VEVENT
UID:online-1
SUMMARY:Online Webinar: DevOps Basics
DTSTART;VALUE=DATE:20260801
LOCATION:Online via Zoom
END:VEVENT
BEGIN:VEVENT
UID:broken-no-start
SUMMARY:Event without a start
END:VEVENT
END:VCALENDAR
"""


def test_parse_ics_maps_canonical_fields():
    recs = parse_ics(
        ICS_SAMPLE,
        source_adapter="meetup_wue_data",
        source_url="https://x/ical",
        default_city="Würzburg",
        default_organizer="WUE Data",
        default_tags=["meetup"],
    )
    # The VEVENT without DTSTART is skipped, not fatal.
    assert len(recs) == 2

    talk = recs[0]
    assert talk.title == "AI Week: Python for Machine Learning"
    assert talk.external_id == "event-12345@meetup.com"
    assert talk.start.isoformat() == "2026-07-10T18:00:00+00:00"
    assert talk.end.isoformat() == "2026-07-10T20:00:00+00:00"
    assert talk.is_online is False
    assert talk.city == "Würzburg"
    assert talk.postal_code == "97080"
    assert talk.venue_name == "ZDI Cube"
    assert (talk.lat, talk.lng) == (49.79, 9.95)
    assert "meetup" in talk.tags and "AI" in talk.tags


def test_parse_ics_detects_online_and_allday():
    recs = parse_ics(ICS_SAMPLE, source_adapter="x", source_url="u")
    online = next(r for r in recs if r.external_id == "online-1")
    assert online.is_online is True
    assert online.city is None  # online events carry no city
    # all-day DATE value becomes midnight Europe/Berlin
    assert online.start.isoformat() == "2026-08-01T00:00:00+02:00"


def test_parse_ics_empty_calendar_is_not_an_error():
    empty = "BEGIN:VCALENDAR\nVERSION:2.0\nEND:VCALENDAR\n"
    assert parse_ics(empty, source_adapter="x", source_url="u") == []


def test_extract_genics_ids_from_listing_html():
    html = (
        '<a href="/x/index.html?_func=genIcs&_eopb=1&_id=1913806">ICS</a> '
        '<a href="/x/index.html?_id=42&_func=genIcs">ICS</a> '
        '<a href="/x/index.html?_func=genIcs&_id=1913806">dup</a>'  # dedup
    )
    assert _extract_genics_ids(html) == ["1913806", "42"]


RSS_SAMPLE = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><title>FRIZZ</title>
<item>
  <title>KI-Hackathon - 15.07.2026 09:00 - 18:00 @ ZDI Cube</title>
  <link>https://frizz-wuerzburg.de/event/123</link>
  <guid>frizz-123</guid>
  <description>Ein Tag voller Code und KI.</description>
  <pubDate>Mon, 21 Apr 2022 07:46:21 +0000</pubDate>
</item>
<item>
  <title>Konzert ohne Datum</title>
  <link>https://frizz-wuerzburg.de/event/456</link>
  <guid>frizz-456</guid>
  <pubDate>Tue, 01 Jun 2026 10:00:00 +0000</pubDate>
</item>
</channel></rss>
"""


def test_parse_rss_prefers_title_date_over_pubdate():
    recs = parse_rss(
        RSS_SAMPLE,
        source_adapter="frizz_wuerzburg",
        source_url="https://frizz-wuerzburg.de/rss",
        default_city="Würzburg",
        default_tags=["frizz"],
        prefer_title_date=True,
    )
    assert len(recs) == 2
    hack = next(r for r in recs if r.external_id == "frizz-123")
    # Event date from the title (Berlin), NOT the 2022 pubDate.
    assert hack.start.isoformat() == "2026-07-15T09:00:00+02:00"
    assert hack.city == "Würzburg"
    assert "frizz" in hack.tags

    # No date in title → falls back to pubDate (UTC).
    concert = next(r for r in recs if r.external_id == "frizz-456")
    assert concert.start.isoformat() == "2026-06-01T10:00:00+00:00"


def test_parse_de_datetime():
    assert parse_de_datetime("Foo - 26.06.2026 18:00 - 19:00").isoformat() == "2026-06-26T18:00:00+02:00"
    assert parse_de_datetime("date only 09.01.2026").isoformat() == "2026-01-09T00:00:00+01:00"
    assert parse_de_datetime("no date here") is None
