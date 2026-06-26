"""Event Radar API — FastAPI application entrypoint."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from . import auth, bookmarks, events, feeds, profile
from .config import settings
from .db import init_db

logger = logging.getLogger("eventradar")


def _guard_secrets() -> None:
    """Fail-fast in production (warn in dev) when security-critical settings are still dev defaults."""
    insecure = settings.insecure_defaults()
    if not insecure:
        return
    fields = ", ".join(insecure)
    if settings.is_production:
        raise RuntimeError(
            f"Refusing to start in production with insecure default secrets: {fields}. "
            "Set real values in the environment."
        )
    logger.warning(
        "Running with insecure DEV default secrets: %s. Fine for local dev; set real values "
        "before deploying (environment=production will refuse to start otherwise).",
        fields,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    _guard_secrets()
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
app.include_router(feeds.router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
