"""Data-driven feed loader — turn feed *definitions* into ready-to-run generic adapters.

A "feed" is a plain RSS/ICS calendar that needs no bespoke parsing: the generic ICSFeedAdapter /
RSSFeedAdapter already cover it. The only thing that varied per feed was a hardcoded ``register(...)``
call. This module removes that: feeds come from two data sources —

  1. ``feeds.yaml`` next to this file (version-controlled defaults), and
  2. the ``feed_sources`` table (runtime-registered via ``POST /api/feeds``),

and both are mapped onto the same two generic adapters. Adding a feed is therefore a config edit or
an API call, never a code change. ``ZdiGenIcsAdapter`` stays a code adapter (discovery + per-event
ICS) and is intentionally absent from the config.

The pure ``looks_like_ics`` / ``looks_like_rss`` validators back the ``POST /api/feeds`` URL check
(fetch a sample, confirm it parses) and are unit-tested without any network.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

import httpx
import yaml

from . import http
from .adapters.ics import ICSFeedAdapter
from .adapters.rss import RSSFeedAdapter
from .base import SourceAdapter

if TYPE_CHECKING:  # avoid importing the DB layer at module load
    from ..models import FeedSource

logger = logging.getLogger("eventradar.ingest.feeds")

FEEDS_YAML = Path(__file__).parent / "feeds.yaml"

_FEED_TYPES = {"ics", "rss"}


# --- Definition → adapter -----------------------------------------------------------------------

def build_adapter(spec: dict[str, Any]) -> SourceAdapter:
    """Build a generic ICS/RSS adapter from one feed definition (dict from YAML or a DB row).

    Raises ``ValueError`` on a missing/invalid required field so a bad config fails loudly at load
    time rather than silently registering nothing.
    """
    name = spec.get("name")
    ftype = spec.get("type")
    if not name or not isinstance(name, str):
        raise ValueError(f"feed definition needs a non-empty 'name': {spec!r}")
    if ftype not in _FEED_TYPES:
        raise ValueError(f"feed {name!r}: 'type' must be one of {sorted(_FEED_TYPES)}, got {ftype!r}")

    urls = spec.get("urls")
    if not urls:
        single = spec.get("url")
        urls = [single] if single else []
    if not urls:
        raise ValueError(f"feed {name!r}: needs 'url' or 'urls'")

    organizer = spec.get("organizer")
    tags = list(spec.get("tags") or [])
    default_city = spec.get("default_city")
    trust_tier = int(spec.get("trust_tier", 2))
    broad = bool(spec.get("broad", ftype == "rss"))

    if ftype == "ics":
        return ICSFeedAdapter(
            name,
            urls,
            broad=broad,
            origin_type="feed",
            trust_tier=trust_tier,
            default_city=default_city,
            default_organizer=organizer,
            default_tags=tags,
        )
    return RSSFeedAdapter(
        name,
        urls[0],
        broad=broad,
        origin_type="feed",
        trust_tier=trust_tier,
        default_city=default_city,
        default_organizer=organizer,
        default_tags=tags,
        prefer_title_date=bool(spec.get("prefer_title_date", False)),
    )


# --- Config feeds (feeds.yaml) ------------------------------------------------------------------

def load_feed_specs(path: Path | None = None) -> list[dict[str, Any]]:
    """Read the YAML feed config into a list of plain dicts. Missing file → empty list."""
    path = path or FEEDS_YAML
    if not path.exists():
        logger.warning("feeds config not found: %s", path)
        return []
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or []
    if not isinstance(data, list):
        raise ValueError(f"feeds config must be a list, got {type(data).__name__}")
    return data


def build_config_feeds(path: Path | None = None) -> list[SourceAdapter]:
    """Build a generic adapter for every feed in feeds.yaml. Returns the adapters (in file order).

    A single malformed entry is logged and skipped — it must not take the whole config (and thus
    every other feed) down with it. The caller (registry) composes these into the live set; this
    function has no side effects of its own.
    """
    adapters: list[SourceAdapter] = []
    for spec in load_feed_specs(path):
        try:
            adapters.append(build_adapter(spec))
        except (ValueError, TypeError) as exc:
            logger.warning("skip invalid feed config entry %r: %s", spec, exc)
            continue
    logger.info("built %d config feed(s): %s", len(adapters), ", ".join(a.name for a in adapters))
    return adapters


# --- DB feeds (feed_sources table) --------------------------------------------------------------

def build_db_feeds(session: Any) -> list[SourceAdapter]:
    """Build a generic adapter for every *enabled* FeedSource row. Returns the adapters.

    The registry layers these on top of the config feeds at ingest time, so a DB feed re-using a
    config name wins. This function only reads the table and builds — it registers nothing.
    """
    from sqlmodel import select

    from ..models import FeedSource

    adapters: list[SourceAdapter] = []
    feeds = session.exec(select(FeedSource).where(FeedSource.enabled == True)).all()  # noqa: E712
    for feed in feeds:
        try:
            adapters.append(build_adapter(_spec_from_db(feed)))
        except (ValueError, TypeError) as exc:
            logger.warning("skip invalid DB feed %r: %s", feed.name, exc)
            continue
    if adapters:
        logger.info("built %d DB feed(s): %s", len(adapters), ", ".join(a.name for a in adapters))
    return adapters


def _spec_from_db(feed: FeedSource) -> dict[str, Any]:
    return {
        "name": feed.name,
        "type": feed.type,
        "url": feed.url,
        "organizer": feed.organizer,
        "tags": feed.tags,
        "default_city": feed.default_city,
        "trust_tier": feed.trust_tier,
        "broad": feed.broad,
    }


# --- URL validation (backs POST /api/feeds) -----------------------------------------------------

def looks_like_ics(text: str) -> bool:
    """True if the text is a parseable VCALENDAR (an empty-but-valid calendar still counts)."""
    if "BEGIN:VCALENDAR" not in text.upper():
        return False
    try:
        from icalendar import Calendar

        Calendar.from_ical(text)
    except (ValueError, IndexError):
        return False
    return True


def looks_like_rss(content: bytes | str) -> bool:
    """True if feedparser recognises the content as an RSS/Atom feed (version set or has entries)."""
    import feedparser

    parsed = feedparser.parse(content)
    return bool(parsed.get("version")) or bool(parsed.get("entries"))


async def validate_feed(ftype: str, url: str) -> tuple[bool, str]:
    """Fetch one sample of ``url`` and confirm it parses as the declared feed ``type``.

    Returns ``(ok, message)``. Network/HTTP failure → ``(False, reason)``; a 200 that does not parse
    as the declared type → ``(False, reason)``. An empty-but-valid calendar/feed is accepted.
    """
    if ftype not in _FEED_TYPES:
        return False, f"unsupported feed type {ftype!r}"
    try:
        async with http.client() as client:
            resp = await client.get(url)
            resp.raise_for_status()
    except httpx.HTTPError as exc:
        return False, f"fetch failed: {exc}"

    if ftype == "ics":
        if looks_like_ics(resp.text):
            return True, "valid ICS calendar"
        return False, "response is not a valid ICS (VCALENDAR) document"
    if looks_like_rss(resp.content):
        return True, "valid RSS/Atom feed"
    return False, "response is not a valid RSS/Atom feed"
