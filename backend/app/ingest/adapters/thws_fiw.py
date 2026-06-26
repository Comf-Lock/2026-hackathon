"""Adapter: THWS — Faculty of Computer Science & Business Information Systems (FIW).

Source #4 in the catalogue. https://fiw.thws.de/termine/ is plain server-rendered HTML: each event
is an accordion `<section>` whose toggle link carries a clean `aria-label`:
    "DD.MM.YYYY[, HH:MM][ bis DD.MM.YYYY|HH:MM] : Title"
The shared `_thws.parse_accordion` parses that structure (the university-wide `thws` adapter reuses
it). IT-native faculty, so `broad = False` (no keyword gate). The FIW sits on the Würzburg campus,
so Würzburg is the default city (overridden only when the text names Schweinfurt).
"""
from __future__ import annotations

from collections.abc import Sequence

from ..registry import register
from ..types import GeoScope, RawEventRecord
from . import _http
from ._thws import parse_accordion

PAGE_URL = "https://fiw.thws.de/termine/"

ORGANIZER = "THWS — Fakultät Informatik und Wirtschaftsinformatik"
# THWS spans Würzburg + Schweinfurt, but the FIW sits at the Würzburg campus
# (Sanderheinrichsleitenweg 20, 97074 Würzburg) → default Würzburg so every event is geocodable.
FIW_DEFAULT_CITY = "Würzburg"


def parse_thws_fiw(html: str, page_url: str = PAGE_URL) -> list[RawEventRecord]:
    """Pure parse: FIW accordion HTML → RawEventRecord list. No network — testable on a fixture."""
    return parse_accordion(
        html,
        page_url=page_url,
        source_adapter="thws_fiw",
        organizer=ORGANIZER,
        trust_tier=1,  # institution / faculty calendar
        default_city=FIW_DEFAULT_CITY,
    )


class ThwsFiwAdapter:
    name = "thws_fiw"
    broad = False  # IT-native faculty — do not gate on title keywords

    async def fetch(self, scope: GeoScope) -> Sequence[RawEventRecord]:
        html = await _http.fetch_text(PAGE_URL)
        return parse_thws_fiw(html, PAGE_URL)


register(ThwsFiwAdapter())
