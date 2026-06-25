"""Events endpoint — a minimal paginated list, for verifying ingestion (slice 2).

Deliberately simple: no user matching, no geo/interest filtering, no auth — that is slice 3+.
Its only job here is to prove the scraper's output reached the store and is readable over HTTP.
Ordered by start ascending so upcoming events come first.
"""
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict
from sqlmodel import Session, func, select

from .db import get_session
from .models import Event

router = APIRouter(prefix="/api/events", tags=["events"])


class EventOut(BaseModel):
    # from_attributes lets us build the response straight from the Event ORM rows.
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    start: object
    end: object | None
    is_online: bool
    city: str | None
    venue_name: str | None
    organizer: str | None
    url: str | None
    image_url: str | None


class EventList(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[EventOut]


@router.get("", response_model=EventList)
async def list_events(
    session: Session = Depends(get_session),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    total = session.exec(select(func.count()).select_from(Event)).one()
    items = session.exec(
        select(Event).order_by(Event.start).offset(offset).limit(limit)
    ).all()
    return EventList(total=total, limit=limit, offset=offset, items=items)
