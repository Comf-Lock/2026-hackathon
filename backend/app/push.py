"""Web Push (Push API / VAPID) — subscription endpoints + a delivery service.

Two halves:
- HTTP routes (auth-gated): the browser registers its ``PushSubscription`` here and removes it on
  unsubscribe. Both are idempotent — the endpoint URL is the unique key, so re-subscribing the same
  browser upserts and unsubscribing something already gone is a no-op.
- ``send_push(session, user, payload)``: encrypts + delivers a payload to every subscription the user
  has, via ``pywebpush``. It is a graceful no-op while no VAPID keypair is configured (settings.push_
  enabled is False), and prunes subscriptions the push service reports as gone (404/410). The actual
  network call lives behind the module-level ``webpush`` name so tests mock it without sending.
"""
from __future__ import annotations

import json
import logging

from fastapi import APIRouter, Depends, Response, status
from pydantic import BaseModel, Field
from pywebpush import WebPushException, webpush
from sqlmodel import Session, select

from .auth import get_current_user
from .config import settings
from .db import get_session
from .models import PushSubscription, User

logger = logging.getLogger("eventradar.push")

router = APIRouter(prefix="/api/push", tags=["push"])


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
