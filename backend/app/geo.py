"""Shared great-circle distance helper (Haversine).

One distance formula for the whole app: the ingest-side geo gate (``ingest.filters.passes_geo``)
and the read-side radius search (``events_service.search_events``) both call this — no second
implementation that could drift.
"""
from __future__ import annotations

from math import asin, cos, radians, sin, sqrt

EARTH_RADIUS_KM = 6371.0


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Great-circle (air-line) distance in km between two (lat, lng) points."""
    dlat, dlng = radians(lat2 - lat1), radians(lng2 - lng1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlng / 2) ** 2
    return 2 * EARTH_RADIUS_KM * asin(sqrt(a))
