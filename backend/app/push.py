"""Web Push (Push API / VAPID) — subscription endpoints + a delivery service.

Three halves:
- HTTP routes: the browser fetches the VAPID public key (``GET /vapid-public-key``, no auth — it is
  public by design), registers/removes its ``PushSubscription`` (auth-gated, idempotent on the endpoint
  URL), and can trigger a test send to itself (``POST /test``, auth-gated).
- ``send_push(session, user, payload)``: encrypts + delivers a payload to every subscription the user
  has, via ``pywebpush``. It is a graceful no-op while no VAPID keypair is configured (settings.push_
  enabled is False), and prunes subscriptions the push service reports as gone (404/410). The actual
  network call lives behind the module-level ``webpush`` name so tests mock it without sending.
- ``generate_vapid_keypair()`` + the ``gen-vapid`` CLI (``python -m app.push gen-vapid``): the *same*
  code that consumes the keys also mints them, so there is no format drift. The private key is emitted
  as the raw 32-byte scalar (base64url) — exactly what ``pywebpush`` feeds to ``Vapid.from_string`` —
  and the public key as the uncompressed 65-byte EC point (base64url), i.e. the ``applicationServerKey``
  the browser's ``pushManager.subscribe`` expects.
"""
from __future__ import annotations

import base64
import json
import logging

from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from fastapi import APIRouter, Depends, Response, status
from py_vapid import Vapid01
from pydantic import BaseModel
from pywebpush import WebPushException, webpush
from sqlmodel import Session, select

from .auth import get_current_user
from .config import settings
from .db import get_session
from .models import PushSubscription, User

logger = logging.getLogger("eventradar.push")

router = APIRouter(prefix="/api/push", tags=["push"])


def _b64url(raw: bytes) -> str:
    """Unpadded URL-safe base64 — the encoding both the VAPID keys and Web Push use throughout."""
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


class _Keys(BaseModel):
    p256dh: str
    auth: str


class PushSubscriptionIn(BaseModel):
    """The browser's ``PushSubscription.toJSON()`` shape: an endpoint plus its encryption keys."""

    endpoint: str
    keys: _Keys


class PushUnsubscribeIn(BaseModel):
    """Unsubscribe payload — identifies the subscription to drop by its endpoint."""

    endpoint: str


class VapidPublicKeyOut(BaseModel):
    """Public VAPID key the frontend passes as ``applicationServerKey`` to ``pushManager.subscribe``."""

    publicKey: str


class TestSendOut(BaseModel):
    """Result of a test send — how many of the user's subscriptions were delivered to."""

    sent: int


@router.get("/vapid-public-key", response_model=VapidPublicKeyOut)
def get_vapid_public_key() -> VapidPublicKeyOut:
    """The VAPID public key (applicationServerKey). No auth — it is public by design.

    Empty string while no keypair is configured; the frontend treats that as "push unavailable".
    """
    return VapidPublicKeyOut(publicKey=settings.vapid_public_key)


@router.post("/subscription", status_code=status.HTTP_204_NO_CONTENT)
def add_subscription(
    body: PushSubscriptionIn,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> Response:
    """Register (or refresh) this browser's push subscription. Idempotent on the endpoint URL.

    The endpoint uniquely identifies one browser install, so a repeat call updates the stored keys and
    re-points the row at the current user instead of creating a duplicate.
    """
    existing = session.exec(
        select(PushSubscription).where(PushSubscription.endpoint == body.endpoint)
    ).first()
    if existing is None:
        session.add(
            PushSubscription(
                user_id=user.id,
                endpoint=body.endpoint,
                p256dh=body.keys.p256dh,
                auth=body.keys.auth,
            )
        )
    else:
        existing.user_id = user.id
        existing.p256dh = body.keys.p256dh
        existing.auth = body.keys.auth
        session.add(existing)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/subscription", status_code=status.HTTP_204_NO_CONTENT)
def remove_subscription(
    body: PushUnsubscribeIn,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> Response:
    """Unsubscribe this browser. Idempotent — removing an unknown endpoint is still a 204.

    Scoped to the current user so one account can never delete another's subscription.
    """
    existing = session.exec(
        select(PushSubscription).where(
            PushSubscription.endpoint == body.endpoint,
            PushSubscription.user_id == user.id,
        )
    ).first()
    if existing is not None:
        session.delete(existing)
        session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/test", response_model=TestSendOut)
def send_test(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> TestSendOut:
    """Send a test notification to all of the current user's subscriptions. Returns the count sent.

    Reuses ``send_push``, so dead/expired subscriptions (410/404) are pruned as a side effect. Returns
    ``sent=0`` when push is disabled (no VAPID keypair) or the user has no subscriptions.
    """
    sent = send_push(
        session,
        user,
        {"title": "Event Radar", "body": "Push funktioniert ✅", "url": "/"},
    )
    return TestSendOut(sent=sent)


def send_push(session: Session, user: User, payload: dict) -> int:
    """Deliver ``payload`` (JSON) to every push subscription ``user`` has. Returns the count sent.

    No-op (returns 0) while push is disabled — no VAPID keypair configured. Subscriptions the push
    service reports as gone (HTTP 404/410) are pruned so a stale browser registration is cleaned up on
    the next send instead of erroring forever. Other delivery errors are logged and skipped, never
    raised, so one dead endpoint can't sink a batch.
    """
    if not settings.push_enabled:
        logger.warning("send_push skipped: no VAPID keypair configured (set VAPID_* in .env)")
        return 0

    subs = session.exec(
        select(PushSubscription).where(PushSubscription.user_id == user.id)
    ).all()
    data = json.dumps(payload)
    sent = 0
    for sub in subs:
        try:
            webpush(
                subscription_info={
                    "endpoint": sub.endpoint,
                    "keys": {"p256dh": sub.p256dh, "auth": sub.auth},
                },
                data=data,
                vapid_private_key=settings.vapid_private_key,
                vapid_claims={"sub": settings.vapid_subject},
            )
            sent += 1
        except WebPushException as exc:
            gone = exc.response is not None and exc.response.status_code in (404, 410)
            if gone:
                logger.info("Pruning gone push subscription %s", sub.endpoint)
                session.delete(sub)
            else:
                logger.warning("Push delivery failed for %s: %s", sub.endpoint, exc)
    if sent < len(subs):
        session.commit()  # persist any prunes
    return sent


def generate_vapid_keypair() -> tuple[str, str]:
    """Mint a fresh VAPID keypair as ``(public_key, private_key)`` base64url strings.

    Same formats the app consumes — private = raw 32-byte scalar (what ``pywebpush`` hands to
    ``Vapid.from_string`` → ``from_raw``); public = uncompressed 65-byte EC point (the browser's
    ``applicationServerKey``). Generating and consuming in one codebase removes any format mismatch.
    """
    vapid = Vapid01()
    vapid.generate_keys()
    private_raw = vapid.private_key.private_numbers().private_value.to_bytes(32, "big")
    public_point = vapid.public_key.public_bytes(Encoding.X962, PublicFormat.UncompressedPoint)
    return _b64url(public_point), _b64url(private_raw)


def _print_vapid_env() -> None:
    """Print a fresh keypair as ready-to-paste ``.env`` lines (consumed by the gen-vapid CLI)."""
    public, private = generate_vapid_keypair()
    print(f"VAPID_PUBLIC_KEY={public}")
    print(f"VAPID_PRIVATE_KEY={private}")
    print("VAPID_SUBJECT=mailto:admin@event-radar.local")


if __name__ == "__main__":
    import sys

    if len(sys.argv) == 2 and sys.argv[1] == "gen-vapid":
        _print_vapid_env()
    else:
        print("usage: python -m app.push gen-vapid", file=sys.stderr)
        sys.exit(2)
