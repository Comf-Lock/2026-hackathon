"""HTTP-level test for GET /api/events.

The ingestion suite covers parsing/filter/upsert, but nothing exercised the events endpoint over
HTTP — and a missing `from_attributes` on EventOut meant serialising ORM rows raised a 500 that the
unit tests never saw. This test closes that gap: it drives the real FastAPI app with an in-memory
DB and asserts the response shape the frontend's useEventSearch contract depends on.
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.db import get_session
from app.main import app
from app.models import Event


@pytest.fixture
def client():
    # StaticPool keeps the single in-memory DB alive across connections, so the seed and the
    # request-scoped sessions opened by the override share the same tables.
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as s:
        s.add_all([
            Event(title="FrankenJS Vue 3", start=datetime(2026, 7, 18, 19, tzinfo=timezone.utc), city="Würzburg"),
            Event(title="THWS Summit", start=datetime(2026, 7, 21, 9, tzinfo=timezone.utc), city="Schweinfurt", is_online=False),
            Event(title="AI Remote Night", start=datetime(2026, 7, 15, 19, tzinfo=timezone.utc), is_online=True),
        ])
        s.commit()

    def _override():
        with Session(engine) as s:
            yield s

    app.dependency_overrides[get_session] = _override
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_list_events_serialises_orm_rows(client):
    # The regression: constructing EventOut from Event ORM objects must not 500.
    r = client.get("/api/events")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 3
    assert {"total", "limit", "offset", "items"} <= body.keys()
    item = body["items"][0]
    # Contract fields the frontend reads.
    assert {"id", "title", "start", "is_online", "city", "venue_name", "url"} <= item.keys()
    # Ordered by start ascending → AI Remote Night (15.) comes first.
    assert [e["title"] for e in body["items"]] == ["AI Remote Night", "FrankenJS Vue 3", "THWS Summit"]


def test_list_events_pagination(client):
    r = client.get("/api/events?limit=1&offset=1")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 3
    assert body["limit"] == 1 and body["offset"] == 1
    assert len(body["items"]) == 1
    assert body["items"][0]["title"] == "FrankenJS Vue 3"
