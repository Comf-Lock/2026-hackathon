"""Filter-stage unit tests — the geo + keyword gates in app.ingest.filters.

Locks the keyword word-boundary fix: short keywords (ai/ki/ml) must match only as whole words,
not as substrings inside unrelated words ("rep-ai-r", "Jam-ai-ka"), while longer keywords still
match inside German compounds.
"""
from __future__ import annotations

from datetime import datetime, timezone

from app.ingest.filters import passes_geo, passes_keyword
from app.ingest.types import GeoScope, RawEventRecord


def _rec(title: str = "Event", **kw) -> RawEventRecord:
    return RawEventRecord(
        source_adapter="t", source_url="https://x/y", title=title,
        start=datetime(2026, 7, 1, tzinfo=timezone.utc), **kw,
    )


def test_short_keyword_matches_only_whole_word():
    scope = GeoScope()
    assert passes_keyword(_rec("KI Salon Würzburg"), scope)[0]
    assert passes_keyword(_rec("Evolving Beyond Code in the Age of AI"), scope)[0]


def test_short_keyword_no_substring_false_positive():
    scope = GeoScope()
    # "ai" must NOT match inside "repair" / "Jamaikanischer".
    assert not passes_keyword(_rec("BIKE REPAIR BASIC WORKSHOP"), scope)[0]
    assert not passes_keyword(_rec("Jamaikanischer Grill-Abend"), scope)[0]
    assert not passes_keyword(_rec("Rave to Save"), scope)[0]


def test_longer_keyword_still_matches_german_compound():
    scope = GeoScope()
    # "daten" should still match inside "Datenanalyse" (substring kept for 4+ char keywords).
    assert passes_keyword(_rec("Praxis-Workshop Datenanalyse"), scope)[0]


def test_geo_postal_prefix_fallback():
    scope = GeoScope()
    # No coordinates, only a postal code: 97/63 prefixes are in scope, others are not.
    assert passes_geo(_rec(postal_code="97070"), scope)[0]       # Würzburg
    assert passes_geo(_rec(postal_code="63739"), scope)[0]       # Aschaffenburg (Untermain)
    assert not passes_geo(_rec(postal_code="90402"), scope)[0]   # Nürnberg — out


def test_geo_coordinates_win_over_radius():
    scope = GeoScope()  # radius 75 km
    assert passes_geo(_rec(lat=49.79, lng=9.95), scope)[0]        # Würzburg centre
    assert not passes_geo(_rec(lat=49.45, lng=11.05), scope)[0]   # Nürnberg ~90 km — out


def test_geo_unknown_passes_for_trusted_regional_source():
    # No geo signal at all → kept (regional-source assumption); this is what lets THWS events
    # with city=None through. Deliberately NOT the strict "blank = drop" stance.
    assert passes_geo(_rec(), GeoScope())[0]
