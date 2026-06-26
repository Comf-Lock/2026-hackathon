"""API response schemas — the single source of truth for the public event shape.

These Pydantic models define the JSON contract both frontends (index + dashboard) consume. They
live here (not on a router) so any consumer — the events router, the bookmarks router, the service
layer — imports the *one* shape, with no router→router coupling.
"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SourceOut(BaseModel):
    """One provenance row — where this event was found during scraping/ingestion.

    The frontend's source-reconciliation row maps ``adapter`` to a platform label/colour. Once
    cross-source dedup lands an event carries several of these; today it is usually one.
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
    # LLM weighting (slice 4): {slug: int} mixes summing to 100 per axis; empty until scored.
    # score_confidence is 0..1 — the frontend marks the bar "geschätzt" when it is low/absent.
    topic_weights: dict = {}
    intent_weights: dict = {}
    score_confidence: float | None = None
    # Attendance / RSVP popularity (enrichment.attendance): a real attendee count from the source
    # platform (Luma guest_count / Meetup "going"). None when no source exposes a number; the card
    # shows a discreet "👥 ~N Teilnehmer" indicator only when present. attendance_source names the
    # platform that supplied it.
    attendee_count: int | None = None
    attendance_source: str | None = None
    sources: list[SourceOut] = []


class EventSearchResponse(BaseModel):
    total: int  # total matches across all pages (for pagination)
    items: list[EventOut]
