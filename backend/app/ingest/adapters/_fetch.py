"""Shared adapter fetch helper: fetch several pages, parse, and dedup across them.

Multi-page scrapers (Meetup group pages, Eventbrite topic listings) all do the same thing: fetch
each URL, parse it to records, and drop duplicates that appear on more than one page — the listings
overlap. That loop was copy-pasted per adapter; this is the one implementation.
"""
from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence

from ..types import RawEventRecord
from . import _http


async def fetch_pages_deduped(
    urls: Iterable[str],
    parse: Callable[[str], Sequence[RawEventRecord]],
) -> list[RawEventRecord]:
    """Fetch each URL's HTML, ``parse`` it to records, and return them deduped by stable id.

    Dedup key is ``RawEventRecord.stable_external_id()`` so overlapping pages within one run yield a
    record once. Order is preserved (first occurrence wins).
    """
    seen: set[str] = set()
    out: list[RawEventRecord] = []
    for url in urls:
        html = await _http.fetch_text(url)
        for rec in parse(html):
            key = rec.stable_external_id()
            if key not in seen:
                seen.add(key)
                out.append(rec)
    return out
