"""Web Push backend — auth-gated subscribe/unsubscribe (idempotent) + mocked send service."""
from __future__ import annotations

from sqlmodel import select

import app.push as push_mod
from app.auth import get_current_user
from app.main import app
from app.config import settings
from app.models import PushSubscription, User


def _make_user(session, sub="sub-1", email="a@example.de") -> User:
    user = User(google_sub=sub, email=email, display_name="Test User")
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def _sub_body(endpoint="https://push.example.com/abc", p256dh="key-p", auth="key-a") -> dict:
    return {"endpoint": endpoint, "keys": {"p256dh": p256dh, "auth": auth}}


def test_push_subscription_requires_auth(client):
    assert client.post("/api/push/subscription", json=_sub_body()).status_code == 401
    assert client.request(
        "DELETE", "/api/push/subscription", json={"endpoint": "x"}
    ).status_code == 401


def test_subscribe_idempotent_and_updates_keys(client, session):
    user = _make_user(session)
    app.dependency_overrides[get_current_user] = lambda: user
    try:
        assert client.post("/api/push/subscription", json=_sub_body()).status_code == 204
        # same endpoint again → no duplicate, keys refreshed in place
        assert client.post(
            "/api/push/subscription",
            json=_sub_body(p256dh="key-p2", auth="key-a2"),
        ).status_code == 204

        rows = session.exec(select(PushSubscription)).all()
        assert len(rows) == 1
        assert rows[0].p256dh == "key-p2"
        assert rows[0].auth == "key-a2"
        assert rows[0].user_id == user.id
    finally:
        app.dependency_overrides.pop(get_current_user, None)


def test_unsubscribe_idempotent_and_scoped_to_user(client, session):
    owner = _make_user(session, sub="owner", email="owner@example.de")
    other = _make_user(session, sub="other", email="other@example.de")
    session.add(
        PushSubscription(user_id=owner.id, endpoint="https://p/1", p256dh="p", auth="a")
    )
    session.commit()

    # another user cannot delete the owner's subscription (scoped) — still a 204 no-op
    app.dependency_overrides[get_current_user] = lambda: other
    try:
        assert client.request(
            "DELETE", "/api/push/subscription", json={"endpoint": "https://p/1"}
        ).status_code == 204
    finally:
        app.dependency_overrides.pop(get_current_user, None)
    assert session.exec(select(PushSubscription)).all()  # still there

    # the owner can, and deleting again is a no-op
    app.dependency_overrides[get_current_user] = lambda: owner
    try:
        assert client.request(
            "DELETE", "/api/push/subscription", json={"endpoint": "https://p/1"}
        ).status_code == 204
        assert client.request(
            "DELETE", "/api/push/subscription", json={"endpoint": "https://p/1"}
        ).status_code == 204
    finally:
        app.dependency_overrides.pop(get_current_user, None)
    assert session.exec(select(PushSubscription)).all() == []


def test_send_push_disabled_is_noop(session, monkeypatch):
    """With no VAPID keypair, send_push delivers nothing and never touches the network."""
    user = _make_user(session)
    session.add(
        PushSubscription(user_id=user.id, endpoint="https://p/1", p256dh="p", auth="a")
    )
    session.commit()

    called = []
    monkeypatch.setattr(push_mod, "webpush", lambda **kw: called.append(kw))
    monkeypatch.setattr(settings, "vapid_public_key", "")
    monkeypatch.setattr(settings, "vapid_private_key", "")

    assert push_mod.send_push(session, user, {"title": "hi"}) == 0
    assert called == []


def test_send_push_delivers_to_each_subscription(session, monkeypatch):
    user = _make_user(session)
    for i in range(2):
        session.add(
            PushSubscription(user_id=user.id, endpoint=f"https://p/{i}", p256dh="p", auth="a")
        )
    session.commit()

    calls = []
    monkeypatch.setattr(push_mod, "webpush", lambda **kw: calls.append(kw))
    monkeypatch.setattr(settings, "vapid_public_key", "pub")
    monkeypatch.setattr(settings, "vapid_private_key", "priv")

    sent = push_mod.send_push(session, user, {"title": "Neues Event", "body": "x"})
    assert sent == 2
    assert len(calls) == 2
    # payload JSON-encoded, VAPID claims carry the configured subject
    assert '"title": "Neues Event"' in calls[0]["data"]
    assert calls[0]["vapid_claims"]["sub"] == settings.vapid_subject
    assert calls[0]["subscription_info"]["keys"] == {"p256dh": "p", "auth": "a"}


def test_send_push_prunes_gone_subscriptions(session, monkeypatch):
    """A 410 Gone from the push service drops that stale subscription."""
    user = _make_user(session)
    session.add(
        PushSubscription(user_id=user.id, endpoint="https://gone/1", p256dh="p", auth="a")
    )
    session.commit()

    class _Resp:
        status_code = 410

    def _raise(**kw):
        raise push_mod.WebPushException("gone", response=_Resp())

    monkeypatch.setattr(push_mod, "webpush", _raise)
    monkeypatch.setattr(settings, "vapid_public_key", "pub")
    monkeypatch.setattr(settings, "vapid_private_key", "priv")

    assert push_mod.send_push(session, user, {"title": "hi"}) == 0
    assert session.exec(select(PushSubscription)).all() == []
