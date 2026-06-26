"""Bookmarks ("Merken") — a user's saved events.

Auth-gated: every route resolves the current user from the session cookie (get_current_user, 401
otherwise). Saving is idempotent (unique on user_id+event_id). The list reuses the events read
shape (EventOut incl. provenance sources) so the dashboard's "Demnächst gespeichert" rail renders
saved events exactly like the feed cards.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlmodel import Session, select

from .auth import get_current_user
from .db import get_session
from .events import EventOut, sources_for, to_event_out
from .models import Bookmark, Event, User

router = APIRouter(prefix="/api/bookmarks", tags=["bookmarks"])


@router.get("", response_model=list[EventOut])
def list_bookmarks(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> list[EventOut]:
    """The current user's saved events, soonest first."""
    event_ids = session.exec(
        select(Bookmark.event_id).where(Bookmark.user_id == user.id)
    ).all()
    if not event_ids:
        return []
    events = session.exec(
        select(Event).where(Event.id.in_(event_ids)).order_by(Event.start.asc())
    ).all()
    srcs = sources_for(session, events)
    return [to_event_out(e, srcs.get(e.id, [])) for e in events]


@router.post("/{event_id}", status_code=204)
def add_bookmark(
    event_id: int,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> Response:
    """Save an event. Idempotent — saving an already-saved event is a no-op (still 204)."""
    if session.get(Event, event_id) is None:
        raise HTTPException(status_code=404, detail="event not found")
    existing = session.exec(
        select(Bookmark).where(Bookmark.user_id == user.id, Bookmark.event_id == event_id)
    ).first()
    if existing is None:
        session.add(Bookmark(user_id=user.id, event_id=event_id))
        session.commit()
    return Response(status_code=204)


@router.delete("/{event_id}", status_code=204)
def remove_bookmark(
    event_id: int,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> Response:
    """Unsave an event. Idempotent — removing a non-saved event is a no-op (still 204)."""
    existing = session.exec(
        select(Bookmark).where(Bookmark.user_id == user.id, Bookmark.event_id == event_id)
    ).first()
    if existing is not None:
        session.delete(existing)
        session.commit()
    return Response(status_code=204)
