"""Google OAuth (Authorization-Code flow via Authlib) + session-cookie auth.

Flow:
  GET  /api/auth/google/login    -> redirect to Google consent
  GET  /api/auth/google/callback -> exchange code, upsert user, set session cookie
  POST /api/auth/logout          -> clear session
  GET  /api/auth/me              -> current user (or 401)

The session is a signed httpOnly cookie (Starlette SessionMiddleware) holding only the
user id — no token is exposed to the frontend.
"""
import logging

from authlib.integrations.starlette_client import OAuth
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, ConfigDict
from sqlmodel import Session, select

from .config import settings
from .db import get_session
from .models import Profile, User

logger = logging.getLogger("eventradar.auth")


class UserOut(BaseModel):
    """Public shape of the current user — the JSON contract /api/auth/me serves."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    display_name: str
    avatar_url: str | None

oauth = OAuth()
oauth.register(
    name="google",
    client_id=settings.google_client_id,
    client_secret=settings.google_client_secret,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

router = APIRouter(prefix="/api/auth", tags=["auth"])

# The OAuth callback path is fixed — it always runs through the Vite /api proxy. Only the host/scheme
# in front of it varies (localhost vs. the Tailscale HTTPS URL).
OAUTH_CALLBACK_PATH = "/api/auth/google/callback"


def _derive_redirect_uri(request: Request) -> str:
    """Build the OAuth callback URL from the *external* host so localhost and the Tailscale HTTPS URL
    both work without one breaking the other.

    Proxy chain: phone → Tailscale Serve (ts.net:443) → Vite (:5173) → Vite /api proxy → backend.
    The Vite proxy uses ``changeOrigin`` → it rewrites ``Host`` to ``localhost:8000``, so the real
    external host only survives in ``X-Forwarded-Host`` (set by Tailscale Serve) and the scheme in
    ``X-Forwarded-Proto``. Without a forwarded host we fall back to the configured localhost default,
    so plain local dev is unchanged. Authlib stores this value in the session on
    ``authorize_redirect`` and re-validates it on the callback, so deriving it once here is enough.
    """
    xf_host = request.headers.get("x-forwarded-host")
    if not xf_host:
        return settings.oauth_redirect_uri
    xf_proto = request.headers.get("x-forwarded-proto", "https")
    return f"{xf_proto}://{xf_host}{OAUTH_CALLBACK_PATH}"


@router.get("/google/login")
async def google_login(request: Request):
    redirect_uri = _derive_redirect_uri(request)
    logger.debug("oauth login → redirect_uri=%s", redirect_uri)
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/google/callback")
async def google_callback(request: Request, session: Session = Depends(get_session)):
    try:
        token = await oauth.google.authorize_access_token(request)
    except Exception as exc:  # invalid state / network / config error
        logger.warning("OAuth token exchange failed: %s", exc)
        raise HTTPException(status_code=400, detail=f"OAuth exchange failed: {exc}")

    userinfo = token.get("userinfo")
    if not userinfo or "sub" not in userinfo:
        logger.warning("OAuth callback returned no usable userinfo")
        raise HTTPException(status_code=400, detail="No userinfo returned by Google")

    sub = userinfo["sub"]
    user = session.exec(select(User).where(User.google_sub == sub)).first()
    if user is None:
        user = User(
            google_sub=sub,
            email=userinfo.get("email", ""),
            display_name=userinfo.get("name", "") or userinfo.get("email", ""),
            avatar_url=userinfo.get("picture"),
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        session.add(Profile(user_id=user.id))
        session.commit()
        logger.info("registered new user id=%s (%s)", user.id, user.email)

    request.session["user_id"] = user.id
    logger.debug("login established for user id=%s", user.id)
    # After login the user lands on the dashboard (the post-login home).
    return RedirectResponse(url=f"{settings.frontend_url}/dashboard", status_code=303)


@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return {"ok": True}


def get_current_user(
    request: Request, session: Session = Depends(get_session)
) -> User:
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user = session.get(User, user_id)
    if user is None:
        # Session points at a user that no longer exists (deleted/reset DB) — drop the stale cookie.
        logger.info("clearing stale session for missing user id=%s", user_id)
        request.session.clear()
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user
