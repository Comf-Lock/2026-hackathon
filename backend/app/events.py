"""Events search/filter API — the read side both frontends (index + dashboard) consume.

The contract is fixed (Agent-1/Agent-2 build against it): ``GET /api/events`` returns
``{total, items}`` where each item carries every canonical Event field. Filters are ANDed; ``q`` is
a case-insensitive substring over title/description/organizer; ``tag`` (repeatable) keeps an event
if it carries any of the requested tags. Results are sorted by ``start`` ascending and, unless
``date_from`` is given, restricted to upcoming events (start >= today).

Tag filtering happens in Python because ``Event.tags`` is a JSON array and membership is not
portably expressible across SQLite (tests) and Postgres (prod); at regional event volumes loading
the structurally-filtered rows and intersecting in Python is correct and cheap.
"""
from __future__ import annotations

from datetime import date, datetime, time, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy import func, or_
from sqlmodel import Session, select

from .db import get_session
from .models import Event, EventSource

router = APIRouter(prefix="/api/events", tags=["events"])


class SourceOut(BaseModel):
    """One provenance row — where this event was found during scraping/ingestion.

    The frontend's source-reconciliation row maps ``adapter`` to a platform label/colour. Once
    cross-source dedup lands (Slice 5) an event carries several of these; today it is usually one
    (= a "blindspot", surfaced as such in the UI).
    """

    adapter: str
    url: str
    origin_type: str


class EventOut(BaseModel):
    """Public shape of an Event — every canonical field plus its provenance sources."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    start: datetime
    end: datetime | None
    is_online: bool
    venue_name: str | None
    address: str | None
    city: str | None
    postal_code: str | None
    lat: float | None
    lng: float | None
    organizer: str | None
    tags: list[str]
    url: str | None
    image_url: str | None
    price: str | None
    language: str | None
    sources: list[SourceOut] = []


class EventSearchResponse(BaseModel):
    total: int  # total matches across all pages (for pagination)
    items: list[EventOut]


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


@router.get("", response_model=EventSearchResponse)
def search_events(
    q: str | None = Query(default=None, description="free text over title/description/organizer"),
    city: str | None = Query(default=None, description="exact city match"),
    tag: list[str] | None = Query(default=None, description="repeatable; keep if any tag matches"),
    date_from: date | None = Query(default=None, description="start >= date_from"),
    date_to: date | None = Query(default=None, description="start <= date_to"),
    is_online: bool | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    sort: str = Query(default="start", pattern="^start$"),
    session: Session = Depends(get_session),
) -> EventSearchResponse:
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

    # Default to upcoming events unless the caller pins an explicit lower bound.
    if date_from is not None:
        conditions.append(Event.start >= _day_start(date_from))
    else:
        conditions.append(Event.start >= _today_start())
    if date_to is not None:
        conditions.append(Event.start <= _day_end(date_to))

    ordered = select(Event).where(*conditions).order_by(Event.start.asc())

    if tag:
        wanted = set(tag)
        rows = session.exec(ordered).all()
        matched = [e for e in rows if wanted & set(e.tags or [])]
        total = len(matched)
        page = matched[offset : offset + limit]
    else:
        total = session.exec(select(func.count()).select_from(Event).where(*conditions)).one()
        page = session.exec(ordered.offset(offset).limit(limit)).all()

    srcs = sources_for(session, page)
    items = [to_event_out(e, srcs.get(e.id, [])) for e in page]
    return EventSearchResponse(total=total, items=items)


@router.get("/{event_id}", response_model=EventOut)
def get_event(event_id: int, session: Session = Depends(get_session)) -> EventOut:
    """Single event by id — used by the detail view (slice-later)."""
    event = session.get(Event, event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="event not found")
    return to_event_out(event, sources_for(session, [event]).get(event.id, []))
