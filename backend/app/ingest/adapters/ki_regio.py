"""Adapter: KI-Regio Mainfranken — the project's own events page (ki-regio.de/veranstaltungen).

KI-Regio is a funded initiative bringing AI competence to SMEs across Mainfranken (Würzburg, Bad
Kissingen, Bad Neustadt …). Its events page is static WordPress: every event is rendered server-side
as a "Cool Timeline" entry — no RSS/ICS, no JS rendering, so a plain HTML parse suffices (no
Playwright). Each entry carries a date (``.story-time``), a title (``h3.ctlb-block-title``) and a
description (``p.ctlb-block-desc``); the time, when given, sits in the description prose ("ab 14:15
Uhr") and is extracted best-effort.

The page has no per-event detail links, so ``source_url`` points back at the listing and the core
derives a stable external_id from (source_url|title|start). ``broad = False``: every event is the
project's own AI programme, so it must not be dropped by the IT-keyword gate. Kept network-free and
side-effect-free (``parse_ki_regio``) so the parse test runs on a captured fixture.
"""
from __future__ import annotations

import re
from collections.abc import Sequence

from bs4 import BeautifulSoup

from ..registry import register
from ..types import GeoScope, RawEventRecord
from . import _http
from . import _normalize as N
from ._normalize import from_german

PAGE_URL = "https://ki-regio.de/veranstaltungen/"

ORGANIZER = "KI-Regio Mainfranken"

# Mainfranken places KI-Regio events actually name — first match wins, so list specific cities.
_CITIES = ("Würzburg", "Schweinfurt", "Bad Kissingen", "Bad Neustadt", "Kitzingen", "Aschaffenburg")

# A clean "DD.MM.YYYY" in the timeline's time cell. Entries with only a month ("Dezember 2025")
# carry no usable day and are skipped.
_DATE_RE = re.compile(r"(\d{1,2}\.\d{1,2}\.\d{4})")

# A start time embedded in the description prose, "HH:MM Uhr" or German "HH.MM Uhr".
_TIME_RE = re.compile(r"(\d{1,2})[:.](\d{2})\s*Uhr")


def _extract_time(text: str | None) -> str | None:
    """Best-effort 'HH:MM' start time from the description prose, or None when absent/implausible."""
    if not text:
        return None
    m = _TIME_RE.search(text)
    if not m:
        return None
    hour, minute = int(m.group(1)), int(m.group(2))
    if hour > 23 or minute > 59:
        return None
    return f"{hour:02d}:{minute:02d}"


def parse_ki_regio(html: str, page_url: str = PAGE_URL) -> list[RawEventRecord]:
    """Pure parse: KI-Regio Cool-Timeline HTML → RawEventRecord list. No network."""
    soup = BeautifulSoup(html, "html.parser")
    records: list[RawEventRecord] = []

    for entry in soup.select("div.wp-block-cp-timeline-content-timeline-block-child"):
        title_el = entry.select_one("h3.ctlb-block-title")
        time_el = entry.select_one(".story-time")
        if not title_el or not time_el:
            continue
        title = title_el.get_text(" ", strip=True)
        if not title:
            continue

        date_match = _DATE_RE.search(time_el.get_text(" ", strip=True))
        if not date_match:
            continue  # month-only entries ("Dezember 2025") have no usable day → skip

        desc_el = entry.select_one("p.ctlb-block-desc")
        description = desc_el.get_text(" ", strip=True) if desc_el else None

        start = from_german(date_match.group(1), _extract_time(description))

        city = N.pick_city(f"{title} {description or ''}", list(_CITIES), None)
        postal = N.extract_postal(title, description)

        records.append(
            RawEventRecord(
                source_adapter="ki_regio",
                external_id=None,  # no per-event id on the page → core hashes (source_url|title|start)
                source_url=page_url,
                origin_type="scrape",
                trust_tier=2,
                title=title,
                description=description,
                start=start,
                city=city,
                postal_code=postal,
                organizer=ORGANIZER,
                language="de",
                url=page_url,
            )
        )
    return records


class KiRegioAdapter:
    name = "ki_regio"
    # broad=False: every entry is KI-Regio's own AI programme — IT-native, keep all (no keyword gate).
    broad = False

    async def fetch(self, scope: GeoScope) -> Sequence[RawEventRecord]:
        html = await _http.fetch_text(PAGE_URL)
        return parse_ki_regio(html, PAGE_URL)


register(KiRegioAdapter())
