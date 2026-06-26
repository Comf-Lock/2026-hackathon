"""Reusable Playwright harness — render a JS page to final HTML.

Deferred infrastructure for *future* true-SPA sources (IHK/Sweap, AI Week, baiosphere). The three
slice-2 adapters do NOT use it — they fetch static HTML / JSON-in-HTML over httpx. It lives here so
those SPA adapters won't each re-implement browser setup: render_html() launches one headless
Chromium with a realistic UA, navigates, optionally waits for a selector, scrolls to trigger lazy
content, and returns page.content(). Adapters stay testable by parsing the returned HTML with a
pure function — the browser is only the fetch transport, swappable for a saved fixture in tests.

An async adapter calls it off the event loop, e.g. `await asyncio.to_thread(render_html, [url])`.
Playwright is imported lazily, so importing this module never requires the browser to be installed;
only an actual render run needs `python -m playwright install chromium`.
"""
from __future__ import annotations

import logging
from collections.abc import Iterable

from . import http

log = logging.getLogger("eventradar.ingest.browser")

# The realistic desktop UA — bot defences (Eventbrite/Cloudflare) reject the default headless UA.
# Sourced from the single shared HTTP layer so the browser presents the same fingerprint as the
# httpx fetches (no more drift between the two).
_UA = http.HEADERS["User-Agent"]


def render_html(
    urls: Iterable[str],
    *,
    headless: bool = True,
    wait_selector: str | None = None,
    scrolls: int = 4,
    timeout_ms: int = 25_000,
) -> dict[str, str]:
    """Render each URL and return {url: final_html}. Failures map to "" (isolated per URL).

    Playwright is imported lazily so this module loads without it installed — only an actual
    render run needs the browser.
    """
    from playwright.sync_api import sync_playwright

    out: dict[str, str] = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(user_agent=_UA, locale="de-DE")
        page = context.new_page()
        for url in urls:
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
                if wait_selector:
                    try:
                        page.wait_for_selector(wait_selector, timeout=timeout_ms)
                    except Exception:
                        log.warning("selector %r not found on %s", wait_selector, url)
                for _ in range(scrolls):
                    page.mouse.wheel(0, 4000)
                    page.wait_for_timeout(700)
                out[url] = page.content()
            except Exception as exc:
                log.warning("render failed for %s: %s", url, exc)
                out[url] = ""
        context.close()
        browser.close()
    return out
