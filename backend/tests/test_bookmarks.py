"""Bookmarks API — auth-gated save/list/remove, idempotent."""
from __future__ import annotations

from datetime import datetime, timezone

from app.auth import get_current_user
from app.main import app
from app.models import Event, User


def _make_user(session) -> User:
    user = User(google_sub="sub-1", email="a@example.de", display_name="Test User")
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def _make_event(session, title="Würzburg Meetup") -> Event:
    event = Event(title=title, start=datetime(2099, 1, 1, 18, 0, tzinfo=timezone.utc))
    session.add(event)
    session.commit()
    session.refresh(event)
    return event


def test_bookmarks_require_auth(client):
    assert client.get("/api/bookmarks").status_code == 401
    assert client.post("/api/bookmarks/1").status_code == 401


def test_bookmark_add_list_remove_idempotent(client, session):
    user = _make_user(session)
    event = _make_event(session)
    app.dependency_overrides[get_current_user] = lambda: user
    try:
        assert client.get("/api/bookmarks").json() == []

        assert client.post(f"/api/bookmarks/{event.id}").status_code == 204
        # saving twice is a no-op, still 204, no duplicate
        assert client.post(f"/api/bookmarks/{event.id}").status_code == 204

        items = client.get("/api/bookmarks").json()
        assert len(items) == 1
        assert items[0]["id"] == event.id
        assert items[0]["title"] == event.title
        assert "sources" in items[0]  # saved events carry the same EventOut shape as the feed

        assert client.delete(f"/api/bookmarks/{event.id}").status_code == 204
        # removing again is a no-op
        assert client.delete(f"/api/bookmarks/{event.id}").status_code == 204
        assert client.get("/api/bookmarks").json() == []
    finally:
        app.dependency_overrides.pop(get_current_user, None)


def test_bookmark_unknown_event_404(client, session):
    user = _make_user(session)
    app.dependency_overrides[get_current_user] = lambda: user
    try:
        assert client.post("/api/bookmarks/999999").status_code == 404
    finally:
        app.dependency_overrides.pop(get_current_user, None)
