"""Events search/filter API — the read side both frontends (index + dashboard) consume.

The contract is fixed (Agent-1/Agent-2 build against it): ``GET /api/events`` returns
``{total, items}`` where each item carries every canonical Event field. This module is a thin
router: the response shapes live in ``schemas``, the search/serialisation logic in
``events_service``.
"""
from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from . import events_service
from .db import get_session
from .schemas import EventOut, EventSearchResponse

router = APIRouter(prefix="/api/events", tags=["events"])


@router.get("", response_model=EventSearchResponse)
def search_events(
    q: str | None = Query(default=None, description="free text over title/description/organizer"),
    city: str | None = Query(default=None, description="exact city match"),
    tag: list[str] | None = Query(default=None, description="repeatable; keep if any tag matches"),
    date_from: date | None = Query(default=None, description="start >= date_from"),
    date_to: date | None = Query(default=None, description="start <= date_to"),
    is_online: bool | None = Query(default=None),
    upcoming: bool = Query(
        default=False,
        description="only ongoing/upcoming events (effective end >= today); default also returns past",
    ),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    sort: str = Query(default="start", pattern="^start$"),
    session: Session = Depends(get_session),
) -> EventSearchResponse:
    return events_service.search_events(
        session,
        q=q,
        city=city,
        tag=tag,
        date_from=date_from,
        date_to=date_to,
        is_online=is_online,
        upcoming=upcoming,
        limit=limit,
        offset=offset,
    )


@router.get("/{event_id}", response_model=EventOut)
def get_event(event_id: int, session: Session = Depends(get_session)) -> EventOut:
    """Single event by id — used by the detail view (slice-later)."""
    event = events_service.get_event(session, event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="event not found")
    return event
