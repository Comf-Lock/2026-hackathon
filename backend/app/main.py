"""Event Radar API — FastAPI application entrypoint."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from . import auth, bookmarks, events, profile
from .config import settings
from .db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Event Radar API", version="0.1.0", lifespan=lifespan)

# Signed httpOnly session cookie. same_site=lax lets the cookie ride the top-level
# redirect back from Google to /api/auth/google/callback.
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.session_secret,
    same_site="lax",
    https_only=False,
)

# Allow the Vite dev frontend to call the API with credentials (cookies).
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(events.router)
app.include_router(bookmarks.router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
