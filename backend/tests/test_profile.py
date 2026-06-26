"""Profile API — read + update of interests/expertise/home/radius.

Auth is provided by overriding ``get_current_user`` with a fixture user (same pattern as the feeds
API tests). The geocoder is monkeypatched so the suite never hits Nominatim.
"""
from __future__ import annotations

import pytest

from app import profile as profile_module
from app.auth import get_current_user
from app.main import app
from app.models import User


def _make_user(session) -> User:
    user = User(google_sub="profile-user", email="user@example.de", display_name="User")
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


@pytest.fixture(autouse=True)
def fake_geocode(monkeypatch):
    """Würzburg → fixed coords; anything else → no hit. Keeps the PUT offline + deterministic."""
    async def _geocode(label: str):
        return (49.7913, 9.9534) if label and "würzburg" in label.lower() else None

    monkeypatch.setattr(profile_module, "geocode", _geocode)


def test_get_creates_empty_profile(client, auth):
    r = client.get("/api/profile")
    assert r.status_code == 200
    body = r.json()
    assert body["interests"] == []
    assert body["expertise"] == []
    assert body["home_label"] is None
    assert body["radius_km"] == 40


def test_put_persists_and_survives_reload(client, auth):
    payload = {
        "interests": ["Frontend", "AI/ML"],
        "expertise": ["Vue", "Python"],
        "home_label": "Würzburg",
        "radius_km": 75,
    }
    put = client.put("/api/profile", json=payload)
    assert put.status_code == 200
    out = put.json()
    assert out["interests"] == ["Frontend", "AI/ML"]
    assert out["expertise"] == ["Vue", "Python"]
    assert out["radius_km"] == 75
    # Geocoding resolved the home label to coordinates.
    assert out["home_lat"] == pytest.approx(49.7913)
    assert out["home_lng"] == pytest.approx(9.9534)

    # "Reload" — a fresh GET must return exactly what was saved.
    again = client.get("/api/profile").json()
    assert again["interests"] == ["Frontend", "AI/ML"]
    assert again["expertise"] == ["Vue", "Python"]
    assert again["home_label"] == "Würzburg"
    assert again["radius_km"] == 75


def test_put_updates_existing_profile(client, auth):
    client.put(
        "/api/profile",
        json={"interests": ["DevOps"], "expertise": [], "home_label": None, "radius_km": 40},
    )
    # A second update overwrites the lists and clears the home location.
    second = client.put(
        "/api/profile",
        json={"interests": ["Security"], "expertise": ["Rust"], "home_label": None, "radius_km": 20},
    ).json()
    assert second["interests"] == ["Security"]
    assert second["expertise"] == ["Rust"]
    assert second["home_label"] is None
    assert second["home_lat"] is None and second["home_lng"] is None
    assert second["radius_km"] == 20


def test_put_requires_auth(client):
    # No auth override → the endpoint rejects the update.
    r = client.put(
        "/api/profile",
        json={"interests": [], "expertise": [], "home_label": None, "radius_km": 40},
    )
    assert r.status_code == 401
