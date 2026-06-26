"""Adapter: THWS — university-wide events calendar (www.thws.de/termine).

Where ``thws_fiw`` covers only the computer-science faculty, this scrapes the central THWS calendar
— the same server-rendered accordion (``aria-label="DD.MM.YYYY… : Title"``), but spanning all
faculties and both campuses (Würzburg + Schweinfurt). So it carries IT/digital events the faculty
page never lists (Software-Engineering info sessions, "KI im Business", StartUP Slam) alongside many
non-IT ones (open-day, geodesy colloquium). Hence ``broad = True``: the core keyword gate keeps only
the IT-relevant ones.

Reuses ``_thws.parse_accordion`` (one parser, two pages — no duplicate scraping logic). Any event
that also appears on the FIW page is de-duplicated downstream by the core's cross-source fingerprint
(dedup_key), so running both adapters does not create duplicate Events. ``default_city = None``: the
calendar spans both campuses, so we let ``pick_city`` detect Würzburg/Schweinfurt from the text and
otherwise leave it for the regional-source geo assumption rather than guessing a campus.
"""
from __future__ import annotations

from collections.abc import Sequence

from ..registry import register
from ..types import GeoScope, RawEventRecord
from . import _http
from ._thws import parse_accordion

PAGE_URL = "https://www.thws.de/termine/"

ORGANIZER = "THWS — Technische Hochschule Würzburg-Schweinfurt"


def parse_thws(html: str, page_url: str = PAGE_URL) -> list[RawEventRecord]:
    """Pure parse: THWS university accordion HTML → RawEventRecord list. No network."""
    return parse_accordion(
        html,
        page_url=page_url,
        source_adapter="thws",
        organizer=ORGANIZER,
        trust_tier=1,  # institution calendar
        default_city=None,  # spans both campuses — detect from text, don't guess
    )


class ThwsAdapter:
    name = "thws"
    # broad=True: the university-wide calendar mixes all faculties — keep only IT-relevant events.
    broad = True

    async def fetch(self, scope: GeoScope) -> Sequence[RawEventRecord]:
        html = await _http.fetch_text(PAGE_URL)
        return parse_thws(html, PAGE_URL)


register(ThwsAdapter())
