"""Adapter: Startbahn27 — Schweinfurt's startup-ecosystem calendar (startbahn27.de).

The region's coverage is otherwise Würzburg-centric; Startbahn27 (the Schweinfurt Gründerzentrum) is
the central Schweinfurt source — BayStartUP pitches, FLIGHT sessions, KI-Lunch-Pitches, Gründer
events. The site is a static TYPO3 install (no Playwright needed): each month renders a dense grid at
``/<YYYY>/month/<M>`` (note: month is NOT zero-padded — ``/month/6``, not ``/month/06``). Every day
cell with events lists ``<a class="event-calendar__day-event-link" href="/news-events/event-detail/…">``
anchors carrying the title; the start time and full description live on the linked detail page.

We crawl the overview only (one fetch per month) and keep the detail URL as ``url``/``source_url`` —
a second crawl level per event would add the time but multiply requests and make the parser test need
a fixture per event for no real gain at this stage. ``start`` is therefore the event date at midnight
(date-only); enrichment/detail crawling can refine the time later. ``broad = True``: the calendar
mixes IT/startup events with generic business ones (Patentsprechtag, museum after-work), so the core's
keyword gate keeps only the relevant ones — the startup/Gründer/KI keywords pass the ecosystem events.

Spillover days from the adjacent month (``event-calendar__day-other-month``) are skipped: those events
belong to — and are fetched from — that month's own page, so skipping them avoids cross-page dupes.
"""
from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime

from bs4 import BeautifulSoup

from ..registry import register
from ..types import GeoScope, RawEventRecord
from . import _http
from ._normalize import BERLIN, pick_city

BASE_URL = "https://startbahn27.de"
ORGANIZER = "Startbahn27 — Gründerzentrum Schweinfurt"

# Cities to detect in an event title; default to Schweinfurt (where the centre sits) when none named.
_CITIES = ("Schweinfurt", "Würzburg")


def _month_url(year: int, month: int) -> str:
    """Overview URL for a month — month is intentionally NOT zero-padded (the site 404s on '06')."""
    return f"{BASE_URL}/{year}/month/{month}"


def parse_month(html: str, *, year: int, month: int, page_url: str | None = None) -> list[RawEventRecord]:
    """Pure parse: a Startbahn27 month grid → RawEventRecord list. No network.

    The day cell only carries the day number; the year/month come from the page being fetched, so they
    are passed in. Other-month spillover cells are skipped (owned by the neighbouring month's page).
    """
    page_url = page_url or _month_url(year, month)
    soup = BeautifulSoup(html, "html.parser")
    records: list[RawEventRecord] = []

    for cell in soup.select(".event-calendar__day.has-events"):
        classes = cell.get("class") or []
        if "event-calendar__day-other-month" in classes:
            continue  # belongs to the adjacent month — fetched from that month's own page
        date_el = cell.select_one(".event-calendar__day-date")
        if date_el is None:
            continue
        day_text = date_el.get_text(strip=True)
        if not day_text.isdigit():
            continue
        try:
            start = datetime(year, month, int(day_text), tzinfo=BERLIN)
        except ValueError:
            continue  # impossible day number for the month — skip defensively

        for link in cell.select("a.event-calendar__day-event-link[href]"):
            title = link.get_text(" ", strip=True)
            href = (link.get("href") or "").strip()
            if not title or not href:
                continue
            detail_url = href if href.startswith("http") else f"{BASE_URL}{href}"
            # Stable per-occurrence id: the detail path plus the date. Recurring events already carry a
            # month suffix in the slug; appending the date makes re-runs hash identically and keeps two
            # occurrences of the same slug on different days distinct.
            external_id = f"startbahn27:{href.lstrip('/')}@{start.date().isoformat()}"
            city = pick_city(title, list(_CITIES), "Schweinfurt")

            records.append(
                RawEventRecord(
                    source_adapter="startbahn27",
                    external_id=external_id,
                    source_url=detail_url,
                    origin_type="scrape",
                    trust_tier=2,  # curated regional Gründerzentrum calendar
                    title=title,
                    start=start,
                    city=city,
                    organizer=ORGANIZER,
                    language="de",
                    url=detail_url,
                )
            )
    return records


class Startbahn27Adapter:
    name = "startbahn27"
    # broad=True: a mixed startup/business calendar — keep only keyword-relevant events at ingest.
    broad = True

    # How many months to crawl from the current one, inclusive (this month + next two).
    MONTHS_AHEAD = 2

    def _months(self) -> list[tuple[int, int]]:
        """(year, month) tuples for the current month and the next ``MONTHS_AHEAD`` ones."""
        now = datetime.now(BERLIN)
        out: list[tuple[int, int]] = []
        year, month = now.year, now.month
        for _ in range(self.MONTHS_AHEAD + 1):
            out.append((year, month))
            month += 1
            if month > 12:
                month = 1
                year += 1
        return out

    async def fetch(self, scope: GeoScope) -> Sequence[RawEventRecord]:
        records: list[RawEventRecord] = []
        for year, month in self._months():
            html = await _http.fetch_text(_month_url(year, month))
            records.extend(parse_month(html, year=year, month=month))
        return records


register(Startbahn27Adapter())
