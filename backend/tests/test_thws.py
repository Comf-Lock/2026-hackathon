"""THWS university-wide adapter parse tests — pure HTML→records, no network.

Fixture ``thws_termine.html`` is a captured slice of https://www.thws.de/termine/ (the same
server-rendered accordion as the FIW page). Covers a single-time event, a 'bis HH:MM' end time, a
multi-day 'bis DD.MM.YYYY' span, and a non-IT event (the broad keyword gate drops that one at ingest
time — parsing itself stays source-agnostic and keeps all four).
"""
from __future__ import annotations

from app.ingest.adapters.thws import parse_thws
from app.ingest.registry import get_adapters


def test_parse_maps_canonical_fields(fixture_text):
    recs = {r.title: r for r in parse_thws(fixture_text("thws_termine.html"))}
    assert len(recs) == 4  # parser is source-agnostic — keyword filtering is the core's job

    se = recs["Infoveranstaltung Online-Studiengang Software Engineering"]
    assert se.source_adapter == "thws"
    assert se.origin_type == "scrape"
    assert se.external_id == "thws:collapse7392"
    assert se.url == "https://www.thws.de/termine/#collapse7392"
    assert se.organizer == "THWS — Technische Hochschule Würzburg-Schweinfurt"
    assert se.language == "de"
    assert se.start.isoformat() == "2026-06-25T19:00:00+02:00"
    assert se.end is None
    assert se.description and se.description.startswith("Die Fakultät Informatik")


def test_end_time_same_day(fixture_text):
    ki = {r.title: r for r in parse_thws(fixture_text("thws_termine.html"))}["KI im Business clever nutzen"]
    # 'bis 18:30' → end is the same day at that time.
    assert ki.start.isoformat() == "2026-07-16T16:00:00+02:00"
    assert ki.end.isoformat() == "2026-07-16T18:30:00+02:00"
    # teaser names Schweinfurt → city detected as Schweinfurt (default_city is None for this adapter).
    assert ki.city == "Schweinfurt"


def test_multiday_end_date(fixture_text):
    bw = {r.title: r for r in parse_thws(fixture_text("thws_termine.html"))}["Bergwerk Hackathon"]
    # 'bis DD.MM.YYYY' → multi-day span, end on the later date (start time carried over).
    assert bw.start.date().isoformat() == "2026-07-24"
    assert bw.end is not None and bw.end.date().isoformat() == "2026-07-25"


def test_adapter_is_registered():
    names = {a.name for a in get_adapters()}
    assert "thws" in names
    assert "thws_fiw" in names  # both THWS adapters coexist (no double-scrape — deduped downstream)
