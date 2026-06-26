"""Google OAuth (Authorization-Code flow via Authlib) + session-cookie auth.

Flow:
  GET  /api/auth/google/login    -> redirect to Google consent
  GET  /api/auth/google/callback -> exchange code, upsert user, set session cookie
  POST /api/auth/logout          -> clear session
  GET  /api/auth/me              -> current user (or 401)

The session is a signed httpOnly cookie (Starlette SessionMiddleware) holding only the
user id — no token is exposed to the frontend.
"""
from authlib.integrations.starlette_client import OAuth
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlmodel import Session, select

from .config import settings
from .db import get_session
from .models import Profile, User

oauth = OAuth()
oauth.register(
    name="google",
    client_id=settings.google_client_id,
    client_secret=settings.google_client_secret,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.get("/google/login")
async def google_login(request: Request):
    return await oauth.google.authorize_redirect(request, settings.oauth_redirect_uri)


@router.get("/google/callback")
async def google_callback(request: Request, session: Session = Depends(get_session)):
    try:
        token = await oauth.google.authorize_access_token(request)
    except Exception as exc:  # invalid state / network / config error
        raise HTTPException(status_code=400, detail=f"OAuth exchange failed: {exc}")

    userinfo = token.get("userinfo")
    if not userinfo or "sub" not in userinfo:
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

    request.session["user_id"] = user.id
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
        request.session.clear()
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return {
        "id": user.id,
        "email": user.email,
        "display_name": user.display_name,
        "avatar_url": user.avatar_url,
    }
