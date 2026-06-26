"""Event Radar API — FastAPI application entrypoint."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from . import auth, bookmarks, events, feeds, profile, push
from .config import settings
from .db import init_db

logger = logging.getLogger("eventradar")

# Shared log line format for the app's own loggers — matches the ingest CLI so web and CLI output
# read the same way ("LEVEL   eventradar.<area>: message").
_LOG_FORMAT = "%(levelname)-7s %(name)s: %(message)s"


def _configure_logging() -> None:
    """Give the app's ``eventradar.*`` loggers a consistent handler + level under uvicorn.

    Uvicorn configures only its own loggers, so our named loggers (``eventradar.geocode``,
    ``eventradar.ingest`` …) would otherwise inherit the root WARNING level and our INFO lines would
    vanish. We attach one handler to the ``eventradar`` parent and stop propagation so lines are not
    also re-emitted by the root handler. Idempotent — safe across reloads / repeated lifespans.
    """
    app_logger = logging.getLogger("eventradar")
    if not app_logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(_LOG_FORMAT))
        app_logger.addHandler(handler)
        app_logger.propagate = False
    app_logger.setLevel(logging.INFO)


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
    _configure_logging()
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
app.include_router(push.router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
