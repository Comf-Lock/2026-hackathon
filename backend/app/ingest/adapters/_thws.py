"""Shared parser for THWS accordion calendars.

Both the faculty calendar (``fiw.thws.de/termine``) and the university-wide one
(``www.thws.de/termine``) render the same server-side accordion: each event is a
``<a data-toggle="collapse" aria-label="DD.MM.YYYY[, HH:MM][ bis DD.MM.YYYY|HH:MM] : Title">`` with a
short teaser in the header's second row. So one parser drives both adapters; only the provenance
(source_adapter / organizer / trust_tier / default_city) differs per page. Kept network-free and
side-effect-free so each adapter's parse test runs on a fixture.
"""
from __future__ import annotations

import re

from bs4 import BeautifulSoup

from ..types import RawEventRecord
from . import _normalize as N
from ._dates import from_german

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


def parse_accordion(
    html: str,
    *,
    page_url: str,
    source_adapter: str,
    organizer: str,
    trust_tier: int,
    default_city: str | None,
    cities: tuple[str, ...] = ("Schweinfurt", "Würzburg"),
) -> list[RawEventRecord]:
    """Pure parse: THWS accordion HTML → RawEventRecord list. No network.

    ``default_city`` is the campus to assume when the event text names none (the FIW faculty sits in
    Würzburg; the university-wide page spans both campuses, so it passes ``None`` and lets the geo
    filter treat a city-less event as a trusted regional source).
    """
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
        external_id = f"{source_adapter}:{anchor}" if anchor else None
        source_url = f"{page_url}#{anchor}" if anchor else page_url

        # Teaser: the header's second row carries a short <p> description; absent on some entries.
        teaser = None
        rows = link.select(".row")
        if len(rows) > 1:
            p = rows[1].select_one(".col-md-9 p")
            if p:
                teaser = p.get_text(" ", strip=True) or None

        city = N.pick_city(f"{title} {teaser or ''}", list(cities), default_city)
        postal = N.extract_postal(title, teaser)

        records.append(
            RawEventRecord(
                source_adapter=source_adapter,
                external_id=external_id,
                source_url=source_url,
                origin_type="scrape",
                trust_tier=trust_tier,
                title=title,
                description=teaser,
                start=start,
                end=end,
                city=city,
                postal_code=postal,
                organizer=organizer,
                language="de",
                url=source_url,
            )
        )
    return records
