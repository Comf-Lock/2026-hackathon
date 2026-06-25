"""Central relevance filtering — one place, not per adapter.

Two gates:
- geo:     keep online events, events in a scope city, or events whose lat/lng fall inside the
           radius. Events with no geo info at all pass (regional sources are in-region by
           construction; we cannot prove otherwise without geocoding, which is slice 4).
- keyword: only applied to `broad` calendars — title/tags must contain a scope keyword. IT-native
           sources skip this so legitimate events with plain titles are not dropped.

Each check returns (passed, reason) so the ingestion run can log *why* something was dropped.
"""
from __future__ import annotations

import re
from functools import lru_cache
from math import asin, cos, radians, sin, sqrt

from .types import GeoScope, RawEventRecord


def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Great-circle distance in km between two points."""
    r = 6371.0
    dlat, dlng = radians(lat2 - lat1), radians(lng2 - lng1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlng / 2) ** 2
    return 2 * r * asin(sqrt(a))


def passes_geo(record: RawEventRecord, scope: GeoScope) -> tuple[bool, str]:
    if record.is_online:
        return True, "online"

    if record.lat is not None and record.lng is not None:
        dist = _haversine_km(scope.center_lat, scope.center_lng, record.lat, record.lng)
        if dist <= scope.radius_km:
            return True, f"within {dist:.0f}km"
        return False, f"{dist:.0f}km > {scope.radius_km}km radius"

    # Postal code but no coordinates — coarse structural fallback (97xxx Unterfranken, 63xxx
    # Bayerischer Untermain). A wrong-region postal code is a definite out-of-scope signal.
    if record.postal_code:
        pc = record.postal_code.strip()
        if any(pc.startswith(p) for p in scope.postal_prefixes):
            return True, f"postal={pc[:2]}xxx"
        return False, f"postal {pc!r} not in scope"

    if record.city:
        city = record.city.casefold()
        if any(c.casefold() in city or city in c.casefold() for c in scope.cities):
            return True, f"city={record.city}"
        return False, f"city {record.city!r} not in scope"

    # No geo signal at all — cannot prove out-of-scope; let it through (regional-source assumption).
    return True, "geo-unknown"


@lru_cache(maxsize=8)
def _keyword_matcher(keywords: tuple[str, ...]):
    """Compile one regex per keyword set: short keywords (≤3 chars like ai/ki/ml) match only as
    whole words — otherwise "ai" hits "rep**ai**r"/"Jam**ai**ka" — while longer ones match as a
    substring so German compounds ("Daten" in "Datenanalyse") still count.
    """
    parts = []
    for kw in keywords:
        esc = re.escape(kw)
        parts.append(rf"\b{esc}\b" if len(kw) <= 3 else esc)
    return re.compile("|".join(parts), re.IGNORECASE)


def passes_keyword(record: RawEventRecord, scope: GeoScope) -> tuple[bool, str]:
    haystack = " ".join([record.title, *(record.tags or [])])
    m = _keyword_matcher(tuple(scope.keywords)).search(haystack)
    if m:
        return True, f"kw={m.group(0).casefold()}"
    return False, "no IT keyword"


def is_relevant(
    record: RawEventRecord, scope: GeoScope, *, apply_keyword: bool
) -> tuple[bool, str]:
    """Combine the gates. Returns (kept, reason) — reason explains the deciding factor."""
    geo_ok, geo_reason = passes_geo(record, scope)
    if not geo_ok:
        return False, f"geo:{geo_reason}"
    if apply_keyword:
        kw_ok, kw_reason = passes_keyword(record, scope)
        if not kw_ok:
            return False, f"keyword:{kw_reason}"
        return True, f"geo:{geo_reason},keyword:{kw_reason}"
    return True, f"geo:{geo_reason}"
