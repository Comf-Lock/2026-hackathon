"""Event read-side service: serialisation + search/filter/pagination.

The business logic behind ``GET /api/events`` lives here, decoupled from FastAPI so it can be reused
(the bookmarks router serialises events the same way) and unit-tested without HTTP. The router in
``events.py`` is a thin shell that only wires query params to these functions.

Tag filtering happens in Python because ``Event.tags`` is a JSON array and membership is not
portably expressible across SQLite (tests) and Postgres (prod); at regional event volumes loading
the structurally-filtered rows and intersecting in Python is correct and cheap.
"""
from __future__ import annotations

import logging
from datetime import date, datetime, time, timezone

from sqlalchemy import case, func, or_
from sqlmodel import Session, select

from .geo import haversine_km
from .models import Event, EventSource
from .schemas import EventOut, EventSearchResponse, SourceOut

logger = logging.getLogger("eventradar.events")

# Pagination contract — the one place these limits are defined; the router imports them for its
# query-parameter bounds so "what the API accepts" and "what the service defaults to" never drift.
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100


def sources_for(session: Session, events: list[Event]) -> dict[int, list[SourceOut]]:
    """Load provenance rows for a page of events, grouped by event id (one query)."""
    ids = [e.id for e in events if e.id is not None]
    if not ids:
        return {}
    rows = session.exec(select(EventSource).where(EventSource.event_id.in_(ids))).all()
    grouped: dict[int, list[SourceOut]] = {}
    for r in rows:
        grouped.setdefault(r.event_id, []).append(
            SourceOut(adapter=r.source_adapter, url=r.source_url, origin_type=r.origin_type)
        )
    return grouped


def to_event_out(event: Event, sources: list[SourceOut]) -> EventOut:
    out = EventOut.model_validate(event)
    out.sources = sources
    return out


def _day_start(d: date) -> datetime:
    return datetime.combine(d, time.min, tzinfo=timezone.utc)


def _day_end(d: date) -> datetime:
    return datetime.combine(d, time.max, tzinfo=timezone.utc)


def _today_start() -> datetime:
    return datetime.combine(datetime.now(timezone.utc).date(), time.min, tzinfo=timezone.utc)


def search_events(
    session: Session,
    *,
    q: str | None = None,
    city: str | None = None,
    tag: list[str] | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    is_online: bool | None = None,
    upcoming: bool = False,
    center_lat: float | None = None,
    center_lng: float | None = None,
    radius_km: float | None = None,
    limit: int = DEFAULT_PAGE_SIZE,
    offset: int = 0,
) -> EventSearchResponse:
    """Filtered, paginated event search. Filters are ANDed.

    By default every event in the DB is returned — past ones included, because a scraped event still
    listed on its source is worth showing. Ordering: ongoing/upcoming first (soonest first), then past
    (most recent first). An event counts as *not past* while its effective end — ``end``, or ``start``
    for single-day events — is today or later, so multi-day events stay visible on their last day.

    ``upcoming=True`` drops past events (keeps ongoing + upcoming). An explicit ``date_from``/``date_to``
    range overrides the default lower bound.

    **Radius search:** ``center_lat``/``center_lng``/``radius_km`` are only active together. When set,
    results are filtered to events whose ``lat``/``lng`` lie within ``radius_km`` air-line (Haversine)
    of the centre; events *without* coordinates are excluded (we cannot prove they are in range). The
    distance check runs in Python over the structurally-filtered rows — same pattern as the tag gate,
    since ``lat``/``lng`` are plain floats and at regional volumes this is correct and cheap. Without
    a centre/radius the behaviour is unchanged.
    """
    radius_active = center_lat is not None and center_lng is not None and radius_km is not None
    conditions = []
    if q:
        like = f"%{q}%"
        conditions.append(
            or_(
                Event.title.ilike(like),
                Event.description.ilike(like),
                Event.organizer.ilike(like),
            )
        )
    if city:
        conditions.append(Event.city == city)
    if is_online is not None:
        conditions.append(Event.is_online == is_online)

    today = _today_start()
    # Effective end: real end for multi-day events, else the start. An event is "not past" while this
    # is >= today. Comparison runs in SQL (portable across SQLite/Postgres, no naive/aware datetime trap).
    eff_end = func.coalesce(Event.end, Event.start)
    if date_from is not None:
        conditions.append(Event.start >= _day_start(date_from))  # explicit range wins
    elif upcoming:
        conditions.append(eff_end >= today)
    if date_to is not None:
        conditions.append(Event.start <= _day_end(date_to))

    # Sort key: not-past group first; within it soonest-first; past group after it, most-recent-first.
    is_past = eff_end < today
    ordered = (
        select(Event)
        .where(*conditions)
        .order_by(
            is_past,  # False (0) = ongoing/upcoming first, True (1) = past last
            case((eff_end >= today, Event.start)).asc(),  # upcoming: soonest first (past → NULL)
            case((eff_end < today, Event.start)).desc(),  # past: most recent first (upcoming → NULL)
        )
    )

    if tag or radius_active:
        # Any Python-side gate (tag membership and/or radius) forces loading the structurally-filtered
        # rows and paginating in Python — SQL count/offset can't express these portably.
        rows = session.exec(ordered).all()
        if tag:
            wanted = set(tag)
            rows = [e for e in rows if wanted & set(e.tags or [])]
        if radius_active:
            rows = [
                e
                for e in rows
                if e.lat is not None
                and e.lng is not None
                and haversine_km(center_lat, center_lng, e.lat, e.lng) <= radius_km
            ]
        total = len(rows)
        page = rows[offset : offset + limit]
    else:
        total = session.exec(select(func.count()).select_from(Event).where(*conditions)).one()
        page = session.exec(ordered.offset(offset).limit(limit)).all()

    srcs = sources_for(session, page)
    items = [to_event_out(e, srcs.get(e.id, [])) for e in page]
    logger.debug(
        "search_events: total=%d page=%d (offset=%d limit=%d) radius=%s",
        total, len(items), offset, limit,
        f"{radius_km}km@({center_lat},{center_lng})" if radius_active else "off",
    )
    return EventSearchResponse(total=total, items=items)


def get_event(session: Session, event_id: int) -> EventOut | None:
    """Serialise a single event by id (with its sources), or None if it doesn't exist."""
    event = session.get(Event, event_id)
    if event is None:
        return None
    return to_event_out(event, sources_for(session, [event]).get(event.id, []))
