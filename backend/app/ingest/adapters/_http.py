"""Shared HTTP fetch for static / JSON-in-HTML adapters.

Adapters split fetch from parse: fetch() does the network I/O via this helper, the parse_*()
functions are pure (html/json string -> RawEventRecord) so the tests run on stored fixtures with
no live network. A realistic browser User-Agent + Accept-Language keeps moderately bot-shy sources
(Eventbrite, Meetup) happy at low frequency; SPA sources that need a real browser are slice-5
(Playwright harness), not here.
"""
from __future__ import annotations

import httpx

# A plausible desktop-Chrome fingerprint — not evasion, just avoiding the trivial "python-httpx"
# block some CDNs apply. We still crawl at low frequency and honour each source's ToS.
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

DEFAULT_TIMEOUT = 25.0


async def fetch_text(url: str, *, timeout: float = DEFAULT_TIMEOUT) -> str:
    """GET `url` and return the decoded body. Raises on HTTP error (caller/core isolates it)."""
    async with httpx.AsyncClient(
        headers=DEFAULT_HEADERS, timeout=timeout, follow_redirects=True
    ) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.text
