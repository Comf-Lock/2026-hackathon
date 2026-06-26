"""Institut-für-Informatik (Uni Würzburg) adapter parse tests — pure HTML→records, no network.

Fixture ``informatik_uni_wue.html`` is a captured slice of the institute's event list
(https://www.informatik.uni-wuerzburg.de/aktuelles/veranstaltungen-und-termine/, 2026-06-26): the
``event-list`` block carrying schema.org microdata. Covers a relative link (resolved to absolute), a
sibling-domain absolute link, a subtitle/speaker teaser, and a title-only entry.
"""
from __future__ import annotations

from app.ingest.adapters.informatik_uni_wue import parse_informatik_uni_wue
from app.ingest.registry import get_adapters


def test_parse_maps_canonical_fields(fixture_text):
    recs = {r.title: r for r in parse_informatik_uni_wue(fixture_text("informatik_uni_wue.html"))}
    assert len(recs) == 5  # every entry in the fixture's event-list

    kol = recs["Offenes Informatikkolloquium"]
    assert kol.source_adapter == "informatik_uni_wue"
    assert kol.origin_type == "scrape"
    assert kol.trust_tier == 1
    assert kol.organizer == "Universität Würzburg — Institut für Informatik"
    assert kol.language == "de"
    assert kol.city == "Würzburg"  # default campus city
    # startDate microdata is naive → stamped Europe/Berlin (CEST in July).
    assert kol.start.isoformat() == "2026-07-08T18:00:00+02:00"
    assert kol.end is None
    # subtitle + speaker after the title become the description.
    assert kol.description == "Warum Drucker Menschen so sehr hassen Christoph Brehm"
    # absolute sibling-domain link kept as-is; external_id derives from it (stable across re-runs).
    assert kol.url == "https://go.uniwue.de/opencolloq"
    assert kol.external_id == "informatik_uni_wue:https://go.uniwue.de/opencolloq"


def test_relative_link_is_resolved_against_page_url(fixture_text):
    recs = {r.title: r for r in parse_informatik_uni_wue(fixture_text("informatik_uni_wue.html"))}
    pp = recs["Projektpräsentation"]
    # href was "/aktuelles/…" → resolved to an absolute URL on the institute domain.
    assert pp.url == (
        "https://www.informatik.uni-wuerzburg.de"
        "/aktuelles/aktuelle-meldungen/single-ifi/news/projektpraesentation/"
    )
    assert pp.start.isoformat() == "2026-07-17T09:00:00+02:00"


def test_title_only_entry_has_no_description(fixture_text):
    recs = {r.title: r for r in parse_informatik_uni_wue(fixture_text("informatik_uni_wue.html"))}
    grad = recs["Graduiertenfeier 2026"]
    assert grad.description is None  # title-only row → no teaser
    assert grad.start.isoformat() == "2026-07-03T16:00:00+02:00"


def test_adapter_is_registered():
    names = {a.name for a in get_adapters()}
    assert "informatik_uni_wue" in names
