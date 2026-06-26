"""Feed-source registration API — the organizer/admin input channel for RSS/ICS feeds.

Auth-gated (every route resolves the current user, 401 otherwise): this is how a logged-in
organizer/admin registers a new event source without a code change (the bridge toward slice-6
organizer self-service). A registered feed is picked up on the next ``python -m app.ingest run``,
which turns each enabled row into a generic adapter (see ingest/feed_loader.register_db_feeds).

POST validates the URL by fetching one sample and confirming it parses as the declared feed type
(an empty-but-valid calendar is accepted) — an unreachable or non-feed URL is a 400, so the registry
never fills with sources that can never ingest.
"""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, ConfigDict
from sqlmodel import Session, select

from .auth import get_current_user
from .db import get_session
from .ingest import feed_loader
from .models import FeedSource, User

router = APIRouter(prefix="/api/feeds", tags=["feeds"])


class FeedIn(BaseModel):
    """Payload to register a feed. Only name/type/url are required; the rest carry sane defaults."""

    name: str
    type: Literal["ics", "rss"]
    url: str
    organizer: str | None = None
    tags: list[str] = []
    default_city: str | None = None
    trust_tier: int = 2
    broad: bool = False


class FeedOut(BaseModel):
    """Public shape of a registered feed."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    type: str
    url: str
    organizer: str | None
    tags: list[str]
    default_city: str | None
    trust_tier: int
    broad: bool
    enabled: bool
    created_at: datetime
    created_by: int | None


@router.get("", response_model=list[FeedOut])
def list_feeds(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> list[FeedSource]:
    """All registered feeds — enabled and disabled — oldest first."""
    return list(session.exec(select(FeedSource).order_by(FeedSource.id.asc())).all())


@router.post("", response_model=FeedOut, status_code=201)
async def create_feed(
    payload: FeedIn,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> FeedSource:
    """Register a feed after validating its URL fetches + parses as the declared type."""
    existing = session.exec(select(FeedSource).where(FeedSource.url == payload.url)).first()
    if existing is not None:
        raise HTTPException(status_code=409, detail="a feed with this URL already exists")

    ok, reason = await feed_loader.validate_feed(payload.type, payload.url)
    if not ok:
        raise HTTPException(status_code=400, detail=f"invalid feed: {reason}")

    feed = FeedSource(
        name=payload.name,
        type=payload.type,
        url=payload.url,
        organizer=payload.organizer,
        tags=payload.tags,
        default_city=payload.default_city,
        trust_tier=payload.trust_tier,
        broad=payload.broad,
        created_by=user.id,
    )
    session.add(feed)
    session.commit()
    session.refresh(feed)
    return feed


@router.delete("/{feed_id}", status_code=204)
def delete_feed(
    feed_id: int,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> Response:
    """Remove a feed. Idempotent — deleting an unknown feed is still 204."""
    feed = session.get(FeedSource, feed_id)
    if feed is not None:
        session.delete(feed)
        session.commit()
    return Response(status_code=204)
