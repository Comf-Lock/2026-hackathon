"""Data-driven feed registry — config loader, migration, DB-feed registration, URL validators.

The generic ICS/RSS *parse* is covered in test_adapters.py; here we test the layer that turns feed
*definitions* (YAML config + DB rows) into registered generic adapters, plus the pure validators
that back POST /api/feeds.
"""
from __future__ import annotations

import pytest

from app.ingest import feed_loader
from app.ingest.adapters.ics import ICSFeedAdapter
from app.ingest.adapters.rss import RSSFeedAdapter
from app.ingest.registry import get_adapters
from app.models import FeedSource

from test_adapters import ICS_SAMPLE, RSS_SAMPLE


# --- build_adapter ------------------------------------------------------------------------------

def test_build_adapter_ics():
    spec = {
        "name": "t_ics",
        "type": "ics",
        "url": "https://example.test/cal.ics",
        "organizer": "Test Org",
        "tags": ["a", "b"],
        "default_city": "Würzburg",
        "trust_tier": 2,
        "broad": False,
    }
    a = feed_loader.build_adapter(spec)
    assert isinstance(a, ICSFeedAdapter)
    assert a.name == "t_ics"
    assert a.urls == ["https://example.test/cal.ics"]
    assert a.broad is False
    assert a.origin_type == "feed"
    assert a.default_tags == ["a", "b"]


def test_build_adapter_ics_accepts_multiple_urls():
    a = feed_loader.build_adapter(
        {"name": "multi", "type": "ics", "urls": ["u1", "u2"]}
    )
    assert isinstance(a, ICSFeedAdapter)
    assert a.urls == ["u1", "u2"]


def test_build_adapter_rss_prefers_title_date():
    a = feed_loader.build_adapter(
        {"name": "t_rss", "type": "rss", "url": "u", "broad": True, "prefer_title_date": True}
    )
    assert isinstance(a, RSSFeedAdapter)
    assert a.broad is True
    assert a.prefer_title_date is True


@pytest.mark.parametrize(
    "spec",
    [
        {"type": "ics", "url": "u"},                       # missing name
        {"name": "x", "type": "atom", "url": "u"},         # bad type
        {"name": "x", "type": "ics"},                      # missing url/urls
    ],
)
def test_build_adapter_rejects_invalid(spec):
    with pytest.raises(ValueError):
        feed_loader.build_adapter(spec)


# --- register_config_feeds ----------------------------------------------------------------------

def test_register_config_feeds_from_temp_yaml(tmp_path):
    cfg = tmp_path / "feeds.yaml"
    cfg.write_text(
        "- name: zz_loader_ics\n"
        "  type: ics\n"
        "  url: https://example.test/a.ics\n"
        "- name: zz_loader_rss\n"
        "  type: rss\n"
        "  url: https://example.test/b.rss\n"
        "- name: zz_broken\n"            # invalid entry must be skipped, not fatal
        "  type: nope\n"
        "  url: https://example.test/c\n",
        encoding="utf-8",
    )
    names = feed_loader.register_config_feeds(cfg)
    assert names == ["zz_loader_ics", "zz_loader_rss"]  # broken one skipped

    registered = {a.name: a for a in get_adapters()}
    assert isinstance(registered["zz_loader_ics"], ICSFeedAdapter)
    assert isinstance(registered["zz_loader_rss"], RSSFeedAdapter)


def test_shipped_feeds_yaml_migration_preserved():
    """The hardcoded Meetup ICS + FRIZZ RSS feeds must survive the move into feeds.yaml."""
    specs = {s["name"]: s for s in feed_loader.load_feed_specs()}
    # 4 Meetup ICS groups + FRIZZ RSS = the previously hardcoded registrations.
    for name in (
        "meetup_wue_data",
        "meetup_wue_softwaredev",
        "meetup_wue_deeplearning",
        "meetup_wue_frontend",
    ):
        assert specs[name]["type"] == "ics"
        assert specs[name]["broad"] is False
    assert specs["frizz_wuerzburg"]["type"] == "rss"
    assert specs["frizz_wuerzburg"]["broad"] is True
    assert specs["frizz_wuerzburg"]["prefer_title_date"] is True


# --- register_db_feeds --------------------------------------------------------------------------

def test_register_db_feeds_only_enabled(session):
    session.add(FeedSource(name="db_enabled", type="ics", url="https://example.test/e.ics"))
    session.add(
        FeedSource(name="db_disabled", type="rss", url="https://example.test/d.rss", enabled=False)
    )
    session.commit()

    names = feed_loader.register_db_feeds(session)
    assert "db_enabled" in names
    assert "db_disabled" not in names  # disabled rows are skipped

    registered = {a.name: a for a in get_adapters()}
    assert isinstance(registered["db_enabled"], ICSFeedAdapter)
    assert registered["db_enabled"].origin_type == "feed"


# --- pure validators (back POST /api/feeds) -----------------------------------------------------

def test_looks_like_ics():
    assert feed_loader.looks_like_ics(ICS_SAMPLE) is True
    assert feed_loader.looks_like_ics("BEGIN:VCALENDAR\nVERSION:2.0\nEND:VCALENDAR\n") is True
    assert feed_loader.looks_like_ics(RSS_SAMPLE) is False
    assert feed_loader.looks_like_ics("<html>not a calendar</html>") is False


def test_looks_like_rss():
    assert feed_loader.looks_like_rss(RSS_SAMPLE) is True
    assert feed_loader.looks_like_rss("just some text, no feed") is False
