"""Ingestion core: scope → adapters → filter → idempotent upsert.

Flow per run: for each registered adapter, fetch() its records for the scope, drop the irrelevant
ones (filters.is_relevant), and upsert the rest keyed on (source_adapter, external_id) so re-runs
update in place instead of duplicating. Failures are isolated: a broken adapter or a single bad
record is logged and skipped, never aborting the whole run. An empty adapter (seasonal festival
out of season) is normal, not an error.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone

from sqlmodel import Session, select

from ..config import settings
from ..models import Event, EventSource
from .dedup import record_fingerprint
from .feed_loader import register_db_feeds
from .filters import is_relevant
from .registry import get_adapters
from .types import GeoScope, RawEventRecord

logger = logging.getLogger("eventradar.ingest")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def default_scope() -> GeoScope:
    """Build the active GeoScope from settings (center/radius); keywords/cities use GeoScope defaults."""
    return GeoScope(
        center_label=settings.ingest_center_label,
        center_lat=settings.ingest_center_lat,
        center_lng=settings.ingest_center_lng,
        radius_km=settings.ingest_radius_km,
    )


@dataclass
class SourceResult:
    source: str
    found: int = 0
    kept: int = 0
    new: int = 0
    updated: int = 0
    error: str | None = None


@dataclass
class IngestionReport:
    scope_label: str
    per_source: list[SourceResult] = field(default_factory=list)

    @property
    def total_new(self) -> int:
        return sum(r.new for r in self.per_source)

    @property
    def total_updated(self) -> int:
        return sum(r.updated for r in self.per_source)


_CANONICAL_FIELDS = (
    "title", "description", "start", "end", "is_online", "venue_name", "address",
    "city", "postal_code", "lat", "lng", "organizer", "tags", "url", "image_url",
    "price", "language",
)


def _apply_record(event: Event, record: RawEventRecord) -> None:
    for f in _CANONICAL_FIELDS:
        setattr(event, f, getattr(record, f))


def _fill_missing(event: Event, record: RawEventRecord) -> None:
    """Backfill only the canonical fields that are still empty on a merged Event — never clobber.

    Used when a second source merges into an existing Event: the first source stays canonical, the
    new one only contributes fields the first one lacked (e.g. an image_url, a city)."""
    for f in _CANONICAL_FIELDS:
        if not getattr(event, f, None):
            new_val = getattr(record, f)
            if new_val:
                setattr(event, f, new_val)


def _attach_source(session: Session, event: Event, record: RawEventRecord, ext_id: str,
                   fetched: datetime) -> None:
    session.add(
        EventSource(
            event_id=event.id,
            source_adapter=record.source_adapter,
            external_id=ext_id,
            source_url=record.source_url,
            fetched_at=fetched,
            origin_type=record.origin_type,
            trust_tier=record.trust_tier,
            raw_payload=record.raw_payload,
        )
    )


def upsert_event(session: Session, record: RawEventRecord) -> bool:
    """Upsert one record. Returns True if a new Event was created, False if an existing one updated.

    Two idempotency lines, in order:
      1. (source_adapter, external_id) on EventSource — same record from the same source → refresh
         in place. Hard guarantee that a re-run never duplicates.
      2. dedup_key (cross-source fingerprint) on Event — the same real-world event from a *different*
         source → attach a new EventSource to the existing Event and backfill missing fields, so
         EventOut.sources reports N sources. Precision-first: only a fingerprint match merges.

    Caller commits.
    """
    ext_id = record.stable_external_id()
    fetched = record.fetched_at or _utcnow()
    dkey = record_fingerprint(record)

    # Line 1: same source + same external id → refresh in place.
    src = session.exec(
        select(EventSource).where(
            EventSource.source_adapter == record.source_adapter,
            EventSource.external_id == ext_id,
        )
    ).first()

    if src is not None:
        event = session.get(Event, src.event_id)
        _apply_record(event, record)
        event.dedup_key = dkey
        event.updated_at = fetched
        src.source_url = record.source_url
        src.fetched_at = fetched
        src.origin_type = record.origin_type
        src.trust_tier = record.trust_tier
        src.raw_payload = record.raw_payload
        session.add(event)
        session.add(src)
        return False

    # Line 2: a different source describing the same event (same fingerprint) → merge.
    existing = session.exec(select(Event).where(Event.dedup_key == dkey)).first()
    if existing is not None:
        _fill_missing(existing, record)
        existing.updated_at = fetched
        session.add(existing)
        _attach_source(session, existing, record, ext_id, fetched)
        return False

    # No match anywhere → new canonical Event + its first source.
    event = Event(dedup_key=dkey)
    _apply_record(event, record)
    session.add(event)
    session.flush()  # assign event.id for the FK
    _attach_source(session, event, record, ext_id, fetched)
    return True


async def run_ingestion(
    session: Session,
    scope: GeoScope | None = None,
    names: list[str] | None = None,
) -> IngestionReport:
    """Run all (or named) adapters once and persist their relevant events. Never raises per source."""
    scope = scope or default_scope()
    report = IngestionReport(scope_label=scope.center_label)
    # Warm code + config-feed adapters, then layer enabled DB feeds on top (DB wins on name clash).
    get_adapters()
    register_db_feeds(session)
    adapters = get_adapters(names)
    logger.info("ingestion start: scope=%s radius=%dkm adapters=%d",
                scope.center_label, scope.radius_km, len(adapters))

    for adapter in adapters:
        result = SourceResult(source=adapter.name)
        try:
            records = list(await adapter.fetch(scope))
        except Exception as exc:  # isolate a broken source — don't abort the run
            result.error = f"{type(exc).__name__}: {exc}"
            logger.warning("adapter %s failed: %s", adapter.name, result.error)
            report.per_source.append(result)
            continue

        result.found = len(records)
        if not records:
            logger.info("adapter %s: no events (ok — may be seasonal/out of season)", adapter.name)

        apply_keyword = getattr(adapter, "broad", False)
        for record in records:
            try:
                kept, reason = is_relevant(record, scope, apply_keyword=apply_keyword)
                if not kept:
                    logger.debug("drop [%s] %r: %s", adapter.name, record.title, reason)
                    continue
                result.kept += 1
                if upsert_event(session, record):
                    result.new += 1
                else:
                    result.updated += 1
            except Exception as exc:  # one bad record must not kill the adapter's batch
                logger.warning("adapter %s: record %r failed: %s", adapter.name, record.title, exc)

        logger.info("adapter %s: found=%d kept=%d new=%d updated=%d",
                    adapter.name, result.found, result.kept, result.new, result.updated)
        report.per_source.append(result)

    session.commit()
    logger.info("ingestion done: new=%d updated=%d", report.total_new, report.total_updated)
    return report
