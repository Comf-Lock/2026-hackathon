"""Adapter: THWS — Faculty of Computer Science & Business Information Systems (FIW).

Source #4 in the catalogue. https://fiw.thws.de/termine/ is plain server-rendered HTML: each event
is an accordion `<section>` whose toggle link carries a clean `aria-label`:
    "DD.MM.YYYY[, HH:MM][ bis DD.MM.YYYY|HH:MM] : Title"
We parse that label for date/time/title and pull the short teaser from the header's second row.
IT-native faculty, so `broad = False` (no keyword gate). Covers Würzburg *and* Schweinfurt campuses;
we leave city unset rather than guess, so the geo filter treats it as a trusted regional source.
"""
from __future__ import annotations

import re
from collections.abc import Sequence

from bs4 import BeautifulSoup

from ..registry import register
from ..types import GeoScope, RawEventRecord
from . import _http
from . import _normalize as N
from ._dates import from_german

PAGE_URL = "https://fiw.thws.de/termine/"

# THWS spans Würzburg + Schweinfurt, but the Fakultät Informatik und Wirtschaftsinformatik (FIW)
# sits at the Würzburg campus (Sanderheinrichsleitenweg 20, 97074 Würzburg). So Würzburg is the
# correct default city for this calendar — only an event whose label/teaser names Schweinfurt
# overrides it. This gives every FIW event a city (→ geocodable for the map) without guessing.
FIW_DEFAULT_CITY = "Würzburg"
_THWS_CITIES = ("Schweinfurt", "Würzburg")

# "22.06.2026  bis 26.06.2026 : Title" / "25.06.2026, 19:00  bis 20:00 : Title" / "01.10.2026 : Title"
_LABEL_RE = re.compile(
    r"^(?P<sd>\d{2}\.\d{2}\.\d{4})"
    r"(?:,\s*(?P<st>\d{1,2}:\d{2}))?"
    r"(?:\s*bis\s*(?P<end>\d{2}\.\d{2}\.\d{4}|\d{1,2}:\d{2}))?"
    r"\s*:\s*(?P<title>.+)$",
    re.S,
)


def _end_datetime(start, end_token, start_time):
    """Turn the 'bis ...' token into an end datetime — a date spans days, a time stays same-day."""
    if not end_token:
        return None
    if "." in end_token:  # DD.MM.YYYY → multi-day event, end at start time on the end date
        return from_german(end_token, start_time)
    hour, minute = (int(p) for p in end_token.split(":"))  # HH:MM → same day, that time
    return start.replace(hour=hour, minute=minute)


def parse_thws_fiw(html: str, page_url: str = PAGE_URL) -> list[RawEventRecord]:
    """Pure parse: accordion HTML → RawEventRecord list. No network — testable on a fixture."""
    soup = BeautifulSoup(html, "html.parser")
    records: list[RawEventRecord] = []

    for link in soup.select('a[data-toggle="collapse"][aria-label]'):
        m = _LABEL_RE.match(link["aria-label"].strip())
        if not m:
            continue
        title = m.group("title").strip()
        if not title:
            continue
        start = from_german(m.group("sd"), m.group("st"))
        end = _end_datetime(start, m.group("end"), m.group("st"))

        # Stable id from the collapse anchor (#collapse1109); source_url points back at the section.
        anchor = (link.get("href") or "").lstrip("#")
        external_id = f"thws_fiw:{anchor}" if anchor else None
        source_url = f"{page_url}#{anchor}" if anchor else page_url

        # Teaser: the header's second row carries a short <p> description; absent on some entries.
        teaser = None
        rows = link.select(".row")
        if len(rows) > 1:
            p = rows[1].select_one(".col-md-9 p")
            if p:
                teaser = p.get_text(" ", strip=True) or None

        # FIW is a Würzburg faculty → default Würzburg, override only if the text names Schweinfurt.
        city = N.pick_city(f"{title} {teaser or ''}", list(_THWS_CITIES), FIW_DEFAULT_CITY)
        postal = N.extract_postal(title, teaser)

        records.append(
            RawEventRecord(
                source_adapter="thws_fiw",
                external_id=external_id,
                source_url=source_url,
                origin_type="scrape",
                trust_tier=1,  # institution / faculty calendar
                title=title,
                description=teaser,
                start=start,
                end=end,
                city=city,
                postal_code=postal,
                organizer="THWS — Fakultät Informatik und Wirtschaftsinformatik",
                language="de",
                url=source_url,
            )
        )
    return records


class ThwsFiwAdapter:
    name = "thws_fiw"
    broad = False  # IT-native faculty — do not gate on title keywords

    async def fetch(self, scope: GeoScope) -> Sequence[RawEventRecord]:
        html = await _http.fetch_text(PAGE_URL)
        return parse_thws_fiw(html, PAGE_URL)


register(ThwsFiwAdapter())
