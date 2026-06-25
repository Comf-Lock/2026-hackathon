"""Geocoding stub — resolves a free-text home location to lat/lng.

Slice 1 calls Nominatim (OpenStreetMap) directly with a low rate. A later slice
caches results in Redis and respects the usage policy more carefully.
"""
import httpx

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"


async def geocode(query: str) -> tuple[float, float] | None:
    params = {"q": query, "format": "json", "limit": 1}
    headers = {"User-Agent": "EventRadar/0.1 (local dev; contact comflock@gmail.com)"}
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            resp = await client.get(NOMINATIM_URL, params=params, headers=headers)
            resp.raise_for_status()
            data = resp.json()
    except Exception:
        return None
    if not data:
        return None
    return float(data[0]["lat"]), float(data[0]["lon"])
