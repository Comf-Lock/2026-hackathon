"""Feeds API — auth-gated register/list/delete, URL validation, dedup.

The live fetch in POST is replaced by patching ``feed_loader.validate_feed`` so the test stays
offline and deterministic; the real fetch+parse is exercised by the pure validators in
test_feed_loader.py.
"""
from __future__ import annotations

import pytest

from app.auth import get_current_user
from app.ingest import feed_loader
from app.main import app
from app.models import User


def _make_user(session) -> User:
    user = User(google_sub="feed-admin", email="admin@example.de", display_name="Admin")
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture
def auth(session):
    user = _make_user(session)
    app.dependency_overrides[get_current_user] = lambda: user
    yield user
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def feed_valid(monkeypatch):
    async def _ok(ftype, url):
        return True, "valid"

    monkeypatch.setattr(feed_loader, "validate_feed", _ok)


def _payload(**over):
    base = {
        "name": "wue_tech_feed",
        "type": "ics",
        "url": "https://example.test/calendar.ics",
        "organizer": "WUE Tech",
        "tags": ["tech", "wue"],
        "default_city": "Würzburg",
    }
    base.update(over)
    return base


def test_feeds_require_auth(client):
    assert client.get("/api/feeds").status_code == 401
    assert client.post("/api/feeds", json=_payload()).status_code == 401
    assert client.delete("/api/feeds/1").status_code == 401


def test_create_lists_and_deletes_feed(client, auth, feed_valid):
    assert client.get("/api/feeds").json() == []

    resp = client.post("/api/feeds", json=_payload())
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["name"] == "wue_tech_feed"
    assert body["type"] == "ics"
    assert body["tags"] == ["tech", "wue"]
    assert body["enabled"] is True
    assert body["created_by"] == auth.id
    feed_id = body["id"]

    listed = client.get("/api/feeds").json()
    assert len(listed) == 1
    assert listed[0]["id"] == feed_id

    assert client.delete(f"/api/feeds/{feed_id}").status_code == 204
    # deleting again is a no-op (idempotent)
    assert client.delete(f"/api/feeds/{feed_id}").status_code == 204
    assert client.get("/api/feeds").json() == []


def test_create_invalid_url_400(client, auth, monkeypatch):
    async def _bad(ftype, url):
        return False, "fetch failed: 404"

    monkeypatch.setattr(feed_loader, "validate_feed", _bad)
    resp = client.post("/api/feeds", json=_payload())
    assert resp.status_code == 400
    assert "invalid feed" in resp.json()["detail"]


def test_create_duplicate_url_409(client, auth, feed_valid):
    assert client.post("/api/feeds", json=_payload()).status_code == 201
    dup = client.post("/api/feeds", json=_payload(name="other_name"))
    assert dup.status_code == 409


def test_create_rejects_unknown_type_422(client, auth, feed_valid):
    # type is a Literal[ics, rss] → pydantic rejects before the handler runs.
    assert client.post("/api/feeds", json=_payload(type="atom")).status_code == 422
