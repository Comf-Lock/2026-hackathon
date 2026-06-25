"""Filter-stage unit tests — the geo + keyword gates in app.ingest.filters.

Locks the keyword word-boundary fix: short keywords (ai/ki/ml) must match only as whole words,
not as substrings inside unrelated words ("rep-ai-r", "Jam-ai-ka"), while longer keywords still
match inside German compounds.
"""
from __future__ import annotations

from datetime import datetime, timezone

from app.ingest.filters import passes_keyword
from app.ingest.types import GeoScope, RawEventRecord


def _rec(title: str) -> RawEventRecord:
    return RawEventRecord(
        source_adapter="t", source_url="https://x/y", title=title,
        start=datetime(2026, 7, 1, tzinfo=timezone.utc),
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
