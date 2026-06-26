"""The single HTTP layer for ingest fetches — one User-Agent, one timeout, one client factory.

Every ingest fetch (static scrapers, ICS/RSS feeds, feed validation, the Playwright UA, geocoding)
goes through here so the anti-bot fingerprint and timeout have exactly one source of truth. They
used to be copy-pasted across five modules and had drifted (Chrome 124/125/126) — that drift is the
bug this consolidates away.

``HEADERS`` is a plausible desktop-Chrome fingerprint: not evasion, just avoiding the trivial
"python-httpx" block some CDNs apply; we still crawl at low frequency and honour each source's ToS.
``client()`` builds a configured ``httpx.AsyncClient`` (callers may override headers/timeout — e.g.
geocoding sends its own identifying Nominatim UA and a shorter timeout). ``fetch_text`` /
``fetch_bytes`` are the thin convenience wrappers; both raise on HTTP error so the ingestion core
can isolate a failing source.
"""
from __future__ import annotations

import httpx

# One anti-bot desktop-Chrome User-Agent. Previously duplicated (and drifting) across the adapters,
# the feed loader and the browser harness — this is now the only place it is defined.
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
    # Broad enough to cover the HTML scrapers, the ICS calendars and the RSS/Atom feeds that each
    # used to send their own Accept — all prior variants were supersets of "*/*", so this is a
    # behaviour-preserving union, not a change.
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "text/calendar,application/rss+xml,*/*;q=0.8"
    ),
}

# One timeout for all ingest fetches. The bot-shy scrapers wanted the most generous value (25s);
# the feed fetches used 20s, so unifying upward only makes a hung request wait marginally longer.
TIMEOUT = httpx.Timeout(25.0)


def client(
    *,
    headers: dict[str, str] | None = None,
    timeout: httpx.Timeout | float | None = None,
    follow_redirects: bool = True,
) -> httpx.AsyncClient:
    """Build an httpx.AsyncClient with the shared UA/timeout. Override headers/timeout when needed."""
    return httpx.AsyncClient(
        headers=HEADERS if headers is None else headers,
        timeout=TIMEOUT if timeout is None else timeout,
        follow_redirects=follow_redirects,
    )


async def fetch_text(url: str, *, timeout: httpx.Timeout | float | None = None) -> str:
    """GET ``url`` and return the decoded body. Raises on HTTP error (caller/core isolates it)."""
    async with client(timeout=timeout) as c:
        resp = await c.get(url)
        resp.raise_for_status()
        return resp.text


async def fetch_bytes(url: str, *, timeout: httpx.Timeout | float | None = None) -> bytes:
    """GET ``url`` and return the raw body bytes. Raises on HTTP error (caller/core isolates it)."""
    async with client(timeout=timeout) as c:
        resp = await c.get(url)
        resp.raise_for_status()
        return resp.content
