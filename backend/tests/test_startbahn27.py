"""Startbahn27 (Schweinfurt) adapter parse tests — pure HTML→records, no network.

Fixture ``startbahn27_month.html`` is the captured calendar grid of https://startbahn27.de/2026/month/6
(static TYPO3). Covers the day-cell → event-link mapping, year/month coming from the fetched page (not
the cell), Schweinfurt-default city detection, and that adjacent-month spillover cells are skipped so
the same event is not also ingested from a neighbouring month's page.
"""
from __future__ import annotations

from app.ingest.adapters.startbahn27 import parse_month
from app.ingest.registry import get_adapters


def _by_title(fixture_text) -> dict:
    recs = parse_month(fixture_text("startbahn27_month.html"), year=2026, month=6)
    return {r.title: r for r in recs}


def test_parse_maps_canonical_fields(fixture_text):
    recs = parse_month(fixture_text("startbahn27_month.html"), year=2026, month=6)
    # 48 in-month events; the 3 spillover events in other-month cells are dropped.
    assert len(recs) == 48
    assert all(r.start.year == 2026 and r.start.month == 6 for r in recs)

    bp = _by_title(fixture_text)["Businessplan Wettbewerb 2026 Phase 3: Q&A"]
    assert bp.source_adapter == "startbahn27"
    assert bp.origin_type == "scrape"
    assert bp.trust_tier == 2
    assert bp.organizer == "Startbahn27 — Gründerzentrum Schweinfurt"
    assert bp.language == "de"
    # Day number from the cell + year/month from the page → date at midnight Europe/Berlin (+02:00 DST).
    assert bp.start.isoformat() == "2026-06-02T00:00:00+02:00"
    assert bp.url == "https://startbahn27.de/news-events/event-detail/businessplan-wettbewerb-2026-phase-3-qa"
    assert bp.source_url == bp.url
    # Stable per-occurrence id: detail path + date.
    assert bp.external_id == (
        "startbahn27:news-events/event-detail/businessplan-wettbewerb-2026-phase-3-qa@2026-06-02"
    )


def test_city_defaults_to_schweinfurt_unless_named(fixture_text):
    by_title = _by_title(fixture_text)
    # No city in the title → the centre's home city, Schweinfurt.
    assert by_title["BayStartUP: Arbeits- und Gesundheitsschutz für Startups"].city == "Schweinfurt"
    # Title names Würzburg → detected over the default.
    assert by_title["Gründerstammtisch Würzburg"].city == "Würzburg"


def test_spillover_other_month_events_are_skipped(fixture_text):
    recs = parse_month(fixture_text("startbahn27_month.html"), year=2026, month=6)
    titles = {r.title for r in recs}
    # These live in event-calendar__day-other-month cells (July) and must NOT appear in the June parse.
    assert "BayStartUP: Pitchen vor Investoren – deine Startup-Story" not in titles
    assert "CIO-Network Mainfranken" not in titles


def test_stable_external_id_is_deterministic(fixture_text):
    a = _by_title(fixture_text)
    b = _by_title(fixture_text)
    assert a["Businessplan Wettbewerb 2026 Phase 3: Q&A"].external_id == \
        b["Businessplan Wettbewerb 2026 Phase 3: Q&A"].external_id


def test_adapter_is_registered():
    by_name = {a.name: a for a in get_adapters()}
    assert "startbahn27" in by_name
    assert by_name["startbahn27"].broad is True
