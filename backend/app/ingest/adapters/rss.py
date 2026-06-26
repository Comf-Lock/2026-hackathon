"""RSS feed adapter — currently the FRIZZ Würzburg city calendar.

FRIZZ is a broad municipal calendar with no IT category, so this adapter is ``broad=True``: the
ingestion core applies the keyword gate to drop non-tech entries. feedparser handles the messy
real-world RSS (encoding, namespaces, date formats); ``parse_rss`` is a pure bytes→records function
so tests run without network. The event date is taken from the entry's published/updated timestamp
— FRIZZ stamps calendar items with their event date — falling back to skipping an entry that has no
usable date at all.
"""
from __future__ import annotations

import logging
import re
from collections.abc import Sequence

import feedparser
import httpx

from .. import http
from ..base import BaseAdapter
from ..types import GeoScope, RawEventRecord
from . import _normalize as N

logger = logging.getLogger("eventradar.ingest.rss")


def _entry_tags(entry: object) -> list[str]:
    raw = getattr(entry, "tags", None) or entry.get("tags", [])  # type: ignore[union-attr]
    out: list[str] = []
    for t in raw or []:
        term = t.get("term") if isinstance(t, dict) else getattr(t, "term", None)
        if term:
            out.append(str(term))
    return out


# Municipal calendars (FRIZZ) append the venue to the title after an " @ ", e.g.
# "KI-Hackathon - 15.07.2026 09:00 @ ZDI Cube". Capture the trailing venue so the map can label it.
_VENUE_AT_RE = re.compile(r"\s+@\s+(?P<venue>[^@]+?)\s*$")


def _venue_from_title(title: str) -> str | None:
    m = _VENUE_AT_RE.search(title)
    return m.group("venue").strip() if m else None


def parse_rss(
    content: bytes | str,
    *,
    source_adapter: str,
    source_url: str,
    origin_type: str = "feed",
    trust_tier: int = 3,
    default_city: str | None = None,
    default_organizer: str | None = None,
    default_tags: list[str] | None = None,
    prefer_title_date: bool = False,
    cities: list[str] | None = None,
) -> list[RawEventRecord]:
    """Parse RSS/Atom content into RawEventRecords. Entries without title/date are skipped.

    With ``prefer_title_date`` the real event date is read from the item title (FRIZZ embeds
    'DD.MM.YYYY HH:MM' there) and the RSS pubDate is only a fallback — otherwise the stored start
    would be the publish date, which the upcoming-events filter would wrongly drop.
    """
    default_tags = default_tags or []
    cities = cities if cities is not None else GeoScope().cities
    feed = feedparser.parse(content)
    records: list[RawEventRecord] = []

    for entry in feed.entries:
        try:
            title = N.clean_text(entry.get("title"))
            published = N.from_struct_time(
                entry.get("published_parsed") or entry.get("updated_parsed")
            )
            title_date = N.parse_de_datetime(title) if prefer_title_date else None
            start = title_date or published
            if not title or start is None:
                continue

            link = entry.get("link") or source_url
            summary = N.clean_text(entry.get("summary") or entry.get("description"))
            ext_id = entry.get("id") or link
            is_online = N.detect_online(title, summary)

            # Pull venue/city/postal out of the free text — a city named in the title/summary wins
            # over the feed default; the default still covers entries that name no city.
            venue_name = None if is_online else _venue_from_title(title)
            city = None if is_online else N.pick_city(f"{title} {summary or ''}", cities, default_city)
            postal = N.extract_postal(title, summary, venue_name)

            records.append(
                RawEventRecord(
                    source_adapter=source_adapter,
                    external_id=ext_id,
                    source_url=link,
                    origin_type=origin_type,
                    trust_tier=trust_tier,
                    title=title,
                    description=summary,
                    start=start,
                    is_online=is_online,
                    venue_name=venue_name,
                    city=city,
                    postal_code=postal,
                    organizer=default_organizer,
                    tags=[*default_tags, *_entry_tags(entry)],
                    url=link,
                )
            )
        except Exception as exc:  # one bad entry must not drop the rest
            logger.warning("skip RSS entry in %s: %s", source_adapter, exc)
            continue
    return records


class RSSFeedAdapter(BaseAdapter):
    """Generic adapter over a single RSS/Atom feed URL."""

    def __init__(
        self,
        name: str,
        url: str,
        *,
        broad: bool = True,
        origin_type: str = "feed",
        trust_tier: int = 3,
        default_city: str | None = None,
        default_organizer: str | None = None,
        default_tags: list[str] | None = None,
        prefer_title_date: bool = False,
    ) -> None:
        self.name = name
        self.url = url
        self.broad = broad
        self.origin_type = origin_type
        self.trust_tier = trust_tier
        self.default_city = default_city
        self.default_organizer = default_organizer
        self.default_tags = default_tags or []
        self.prefer_title_date = prefer_title_date

    async def fetch(self, scope: GeoScope) -> Sequence[RawEventRecord]:
        async with http.client() as client:
            try:
                resp = await client.get(self.url)
                resp.raise_for_status()
            except httpx.HTTPError as exc:
                logger.warning("RSS fetch failed %s: %s", self.url, exc)
                return []
        return parse_rss(
            resp.content,
            source_adapter=self.name,
            source_url=self.url,
            origin_type=self.origin_type,
            trust_tier=self.trust_tier,
            default_city=self.default_city,
            default_organizer=self.default_organizer,
            default_tags=self.default_tags,
            prefer_title_date=self.prefer_title_date,
            cities=scope.cities,
        )


# The FRIZZ RSS feed moved to feeds.yaml (data-driven registration — see ingest/feed_loader.py).
# This module now only provides the generic RSSFeedAdapter + pure parse_rss; nothing self-registers.
