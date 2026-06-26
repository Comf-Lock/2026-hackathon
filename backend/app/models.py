"""Persistence models for Event Radar.

A User is created from the Google identity (google_sub is the stable key). Each user
has exactly one Profile holding their interests/expertise and home location + radius,
which later drives the "events near you" matching.

Ingestion (slice 2) adds the canonical Event plus its EventSource provenance rows: one
Event can be backed by several sources once cross-source dedup lands (slice 5); for now
the scraper produces one source per event. The (source_adapter, external_id) pair is the
idempotency key, so re-runs update in place instead of duplicating.
"""
from datetime import datetime, timezone

from sqlalchemy import JSON, Column, UniqueConstraint
from sqlmodel import Field, SQLModel


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(SQLModel, table=True):
    __tablename__ = "users"  # "user" is a reserved word in Postgres — avoid quoting headaches.

    id: int | None = Field(default=None, primary_key=True)
    google_sub: str = Field(index=True, unique=True)
    email: str
    display_name: str
    avatar_url: str | None = None
    created_at: datetime = Field(default_factory=_utcnow)


class Profile(SQLModel, table=True):
    __tablename__ = "profiles"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", unique=True, index=True)

    # Stored as JSON arrays — DB-agnostic and good enough for slice 1.
    interests: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    expertise: list[str] = Field(default_factory=list, sa_column=Column(JSON))

    home_label: str | None = None
    home_lat: float | None = None
    home_lng: float | None = None
    radius_km: int = 40


class Event(SQLModel, table=True):
    """Canonical event — the deduplicated, source-agnostic record the rest of the app reads.

    lat/lng stay plain floats (like Profile) so the SQLite test path keeps working; the real
    PostGIS geometry column + radius query are introduced in slice 3 where they are actually used.
    """

    __tablename__ = "events"

    id: int | None = Field(default=None, primary_key=True)

    title: str
    description: str | None = None

    # Timezone-aware (Europe/Berlin) start; end is optional.
    start: datetime = Field(index=True)
    end: datetime | None = None
    is_online: bool = False

    # Location — geocoded lat/lng are filled by slice-4 enrichment when missing.
    venue_name: str | None = None
    address: str | None = None
    city: str | None = Field(default=None, index=True)
    postal_code: str | None = None
    lat: float | None = None
    lng: float | None = None

    # Classification — tags are raw source categories/keywords (DB-agnostic JSON array).
    organizer: str | None = None
    tags: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    url: str | None = None
    image_url: str | None = None
    price: str | None = None
    language: str | None = None

    # Cross-source dedup fingerprint (ingest.dedup.event_fingerprint): events sharing this key are
    # the same real-world event seen on different sources and are merged into one Event with several
    # EventSource rows. Indexed — the upsert looks events up by it. None only for legacy rows.
    dedup_key: str | None = Field(default=None, index=True)

    # LLM weighting (slice 4) — topic/intent mixes as {slug: int} summing to 100 per axis,
    # filled by enrichment.score. Empty until scored (or while scoring is disabled). scored_text_hash
    # is the cache key: re-scoring is skipped while it matches the current text → no redundant spend.
    topic_weights: dict = Field(default_factory=dict, sa_column=Column(JSON))
    intent_weights: dict = Field(default_factory=dict, sa_column=Column(JSON))
    score_confidence: float | None = None
    score_model: str | None = None
    scored_text_hash: str | None = None

    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)


class EventSource(SQLModel, table=True):
    """Provenance for where a canonical Event came from.

    Unique on (source_adapter, external_id): the idempotent upsert key. raw_payload keeps the
    original source fields for debugging / re-parsing without re-fetching.
    """

    __tablename__ = "event_sources"
    __table_args__ = (
        UniqueConstraint("source_adapter", "external_id", name="uq_source_adapter_external_id"),
    )

    id: int | None = Field(default=None, primary_key=True)
    event_id: int = Field(foreign_key="events.id", index=True)

    source_adapter: str = Field(index=True)  # e.g. "thws_fiw", "eventbrite_wue", "meetup"
    external_id: str  # stable source id; fallback sha256(source_url|title|start) — see ingest.types
    source_url: str
    fetched_at: datetime = Field(default_factory=_utcnow)

    # origin_type: scrape | feed | api | organizer | crowd — steers trust/moderation downstream.
    origin_type: str = "scrape"
    trust_tier: int = 3  # 1=high (institution/feed) … 3=low (open scrape)

    raw_payload: dict = Field(default_factory=dict, sa_column=Column(JSON))


class FeedSource(SQLModel, table=True):
    """A runtime-registered RSS/ICS feed — the data-driven feed input channel.

    Mirrors a feeds.yaml entry but lives in the DB so feeds can be added via ``POST /api/feeds``
    without a code/config change. At ingest time every ``enabled`` row is turned into a generic
    ICS/RSS adapter (see ingest/feed_loader.register_db_feeds), so its events flow in with
    ``source_adapter = name`` and ``origin_type = "feed"``. Unique on ``url`` — the same feed is
    never registered twice.
    """

    __tablename__ = "feed_sources"
    __table_args__ = (UniqueConstraint("url", name="uq_feed_source_url"),)

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    type: str  # ics | rss
    url: str
    organizer: str | None = None
    tags: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    default_city: str | None = None
    trust_tier: int = 2
    broad: bool = False
    enabled: bool = True
    created_at: datetime = Field(default_factory=_utcnow)
    created_by: int | None = Field(default=None, foreign_key="users.id")


class Bookmark(SQLModel, table=True):
    """A user's saved ("Merken") event. Unique on (user_id, event_id) — saving twice is idempotent."""

    __tablename__ = "bookmarks"
    __table_args__ = (
        UniqueConstraint("user_id", "event_id", name="uq_bookmark_user_event"),
    )

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    event_id: int = Field(foreign_key="events.id", index=True)
    created_at: datetime = Field(default_factory=_utcnow)
