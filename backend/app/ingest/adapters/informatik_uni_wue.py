"""Adapter: Institut für Informatik, Uni Würzburg — events & dates calendar.

https://www.informatik.uni-wuerzburg.de/aktuelles/veranstaltungen-und-termine/ runs its own TYPO3
instance whose event list is **not** mirrored in the central university RSS — a genuine coverage gap
(Informatik-Kolloquien, Projektpräsentationen, the HCI/Games "Sommer Expo"). Plain server-rendered
HTML, so no Playwright: each event is a ``<div class="event-list__entry">`` carrying schema.org
microdata — a ``<meta itemprop="startDate">`` (and optional ``endDate``) plus a
``<span itemprop="name">`` title inside the link. We read those directly, which is sturdier than
scraping the human-readable month/day spans.

IT-native faculty, so ``broad = False`` (no keyword gate). The institute sits on the Würzburg campus,
so Würzburg is the default city. Links are often relative (``/aktuelles/…``) and sometimes point at
sibling domains (``go.uniwue.de``, ``expo.informatik…``) — both are resolved against the page URL.
Kept network-free and side-effect-free so the parse test runs on a captured fixture.
"""
from __future__ import annotations

from collections.abc import Sequence
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from ..registry import register
from ..types import GeoScope, RawEventRecord
from . import _http
from . import _normalize as N
from ._normalize import from_iso

PAGE_URL = "https://www.informatik.uni-wuerzburg.de/aktuelles/veranstaltungen-und-termine/"

ORGANIZER = "Universität Würzburg — Institut für Informatik"
# The institute sits at the Würzburg Hubland campus → default Würzburg so every event is geocodable.
DEFAULT_CITY = "Würzburg"


def _teaser(p_tag, title_span) -> str | None:
    """The subtitle/speaker lines that sit after the title span in the same <p>, or None."""
    parts: list[str] = []
    for s in p_tag.find_all(string=True):
        if title_span in s.parents:  # skip the title's own text node
            continue
        text = s.strip()
        if text:
            parts.append(text)
    return " ".join(parts) or None


def parse_informatik_uni_wue(html: str, page_url: str = PAGE_URL) -> list[RawEventRecord]:
    """Pure parse: institute event-list HTML → RawEventRecord list. No network."""
    soup = BeautifulSoup(html, "html.parser")
    records: list[RawEventRecord] = []

    for entry in soup.select(".event-list__entry"):
        start_meta = entry.select_one('meta[itemprop="startDate"]')
        title_span = entry.select_one('[itemprop="name"]')
        if not start_meta or not title_span:
            continue  # not a parseable event row
        title = title_span.get_text(" ", strip=True)
        start_raw = (start_meta.get("content") or "").strip()
        if not title or not start_raw:
            continue
        start = from_iso(start_raw)

        end_meta = entry.select_one('meta[itemprop="endDate"]')
        end = from_iso(end_meta["content"].strip()) if end_meta and end_meta.get("content") else None

        # Resolve the link (often relative, sometimes a sibling domain) against the page URL.
        link = entry.select_one(".event-list__content a[href]")
        href = urljoin(page_url, link["href"].strip()) if link and link.get("href") else page_url

        # Stable id from the (resolved) link — same event re-runs to the same upsert key.
        external_id = f"informatik_uni_wue:{href}"

        p_tag = link.find("p") if link else None
        teaser = _teaser(p_tag, title_span) if p_tag else None

        city = N.pick_city(f"{title} {teaser or ''}", [DEFAULT_CITY, "Schweinfurt"], DEFAULT_CITY)
        postal = N.extract_postal(title, teaser)

        records.append(
            RawEventRecord(
                source_adapter="informatik_uni_wue",
                external_id=external_id,
                source_url=href,
                origin_type="scrape",
                trust_tier=1,  # institution / faculty calendar
                title=title,
                description=teaser,
                start=start,
                end=end,
                city=city,
                postal_code=postal,
                organizer=ORGANIZER,
                language="de",
                url=href,
            )
        )
    return records


class InformatikUniWueAdapter:
    name = "informatik_uni_wue"
    broad = False  # IT-native faculty — do not gate on title keywords

    async def fetch(self, scope: GeoScope) -> Sequence[RawEventRecord]:
        html = await _http.fetch_text(PAGE_URL)
        return parse_informatik_uni_wue(html, PAGE_URL)


register(InformatikUniWueAdapter())
