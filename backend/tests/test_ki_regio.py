"""KI-Regio Mainfranken adapter parse tests — pure HTML→records, no network.

Fixture ``ki_regio_veranstaltungen.html`` is a captured slice of https://ki-regio.de/veranstaltungen/
(the static WordPress "Cool Timeline"). It holds five entries covering: a date with a time embedded in
the description ("ab 14:15 Uhr"), city detection for Bad Kissingen and Bad Neustadt, an IT event, and
a month-only entry ("Dezember 2025") that the parser must skip for lacking a usable day.
"""
from __future__ import annotations

from app.ingest.adapters.ki_regio import parse_ki_regio
from app.ingest.registry import get_adapters


def test_parse_maps_canonical_fields(fixture_text):
    recs = {r.title: r for r in parse_ki_regio(fixture_text("ki_regio_veranstaltungen.html"))}
    # Five source entries, but the month-only "Dezember 2025" one has no parseable day → skipped.
    assert len(recs) == 4

    pod = recs["Podiumsdiskussion „KI-Regio im Dialog: Künstliche Intelligenz für Unternehmen in Mainfranken“"]
    assert pod.source_adapter == "ki_regio"
    assert pod.origin_type == "scrape"
    assert pod.external_id is None  # no per-event id on the page → core derives the stable hash
    assert pod.source_url == "https://ki-regio.de/veranstaltungen/"
    assert pod.url == "https://ki-regio.de/veranstaltungen/"
    assert pod.organizer == "KI-Regio Mainfranken"
    assert pod.language == "de"
    # time lifted from the description prose ("ab 14:15 Uhr") onto the date from the timeline cell
    assert pod.start.isoformat() == "2026-05-13T14:15:00+02:00"
    assert pod.city == "Würzburg"  # "Audimax der Universität Würzburg" in the description
    assert pod.description and pod.description.startswith("Am 13. Mai 2026")


def test_month_only_entry_is_skipped(fixture_text):
    titles = {r.title for r in parse_ki_regio(fixture_text("ki_regio_veranstaltungen.html"))}
    assert not any(t.startswith("Bewilligung des EXIST") for t in titles)


def test_date_only_event_starts_at_midnight(fixture_text):
    recs = {r.title: r for r in parse_ki_regio(fixture_text("ki_regio_veranstaltungen.html"))}
    # No "HH:MM Uhr" in this entry's description → start stays date-only (midnight Europe/Berlin).
    abas = recs["ABAS-EUG Tagung in Bad Kissingen"]
    assert abas.start.isoformat() == "2026-03-13T00:00:00+01:00"  # March → CET (+01:00)
    assert abas.city == "Bad Kissingen"
    assert abas.end is None


def test_city_detection_bad_neustadt(fixture_text):
    recs = {r.title: r for r in parse_ki_regio(fixture_text("ki_regio_veranstaltungen.html"))}
    barcamp = next(r for t, r in recs.items() if t.startswith("Unternehmer-BARCAMP"))
    assert barcamp.city == "Bad Neustadt"


def test_adapter_is_registered_and_not_broad():
    adapters = {a.name: a for a in get_adapters()}
    assert "ki_regio" in adapters
    # IT-native source: keep all events, do not subject them to the keyword gate.
    assert adapters["ki_regio"].broad is False
