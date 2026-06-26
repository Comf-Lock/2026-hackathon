"""Settings for the Event Radar API — loaded from environment / .env.

Google OAuth credentials default to placeholders so the whole app builds and runs
without a real client; Lars fills in the real values in .env when login is tested.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict

# Insecure dev defaults, named so the startup secrets-guard can compare against the *same*
# literals the fields default to — no drift between "what we ship" and "what we warn about".
DEV_SESSION_SECRET = "dev-insecure-session-secret-change-me"
DEV_GOOGLE_CLIENT_ID = "PLACEHOLDER_GOOGLE_CLIENT_ID"
DEV_GOOGLE_CLIENT_SECRET = "PLACEHOLDER_GOOGLE_CLIENT_SECRET"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Deployment environment. "production" makes the startup secrets-guard fail-fast instead of
    # only warning, so a misconfigured prod deploy never boots with dev placeholder secrets.
    environment: str = "development"

    # Database — local default points at the docker-compose postgres on localhost.
    # Inside docker-compose this is overridden to host "db".
    database_url: str = "postgresql+psycopg://eventradar:eventradar@localhost:5432/eventradar"

    # Signed session cookie (httpOnly) — change in production.
    session_secret: str = DEV_SESSION_SECRET

    # Google OAuth — placeholders until Lars creates the OAuth client.
    google_client_id: str = DEV_GOOGLE_CLIENT_ID
    google_client_secret: str = DEV_GOOGLE_CLIENT_SECRET
    oauth_redirect_uri: str = "http://localhost:8000/api/auth/google/callback"

    # Where to send the browser back to after a successful login.
    frontend_url: str = "http://localhost:5173"

    # --- Ingestion search scope (slice 2) ---
    # Default fixed to Mainfranken (Würzburg centre); override via .env to widen the scope
    # without code changes (goal: later global). Keywords/cities live on GeoScope defaults.
    ingest_center_label: str = "Würzburg"
    ingest_center_lat: float = 49.7913
    ingest_center_lng: float = 9.9534
    ingest_radius_km: int = 60

    # --- Geocoding (Nominatim / OpenStreetMap) ---
    # Nominatim's usage policy requires an identifying User-Agent (app + contact) and at most
    # 1 request/second. Both are configurable so a deployment can set its own contact + endpoint.
    nominatim_url: str = "https://nominatim.openstreetmap.org/search"
    nominatim_user_agent: str = "EventRadar/0.1 (Mainfranken event radar; contact comflock@gmail.com)"
    nominatim_min_interval_s: float = 1.0

    # --- LLM event weighting (slice 4) ---
    # Empty key disables scoring gracefully (enrichment.score.is_enabled() == False) — the app
    # still builds and runs, events just keep empty weights and the frontend shows placeholders.
    anthropic_api_key: str = ""
    score_model: str = "claude-haiku-4-5"

    # --- Attendance / RSVP popularity signal ---
    # Luma exposes its guest_count publicly (no key). Meetup's "going" count is preferred straight
    # from the already-scraped page; only when that is absent do we fall back to Meetup's GraphQL
    # API, which needs an OAuth token. Empty key disables just that API fallback — everything else
    # (Luma + scraped Meetup counts) keeps working with no key.
    meetup_api_key: str = ""

    # --- Web Push (VAPID / Push API) ---
    # The VAPID keypair authenticates this server to the browser push services. Generate once with
    # `vapid --gen` (py-vapid) and put the values in .env — never commit real keys. The public key is
    # also handed to the frontend so it can subscribe; the subject is a mailto:/https: contact URL.
    # All empty by default → send_push() is a graceful no-op (push disabled) until keys are set.
    vapid_public_key: str = ""
    vapid_private_key: str = ""
    vapid_subject: str = "mailto:comflock@gmail.com"

    @property
    def push_enabled(self) -> bool:
        """True once a VAPID keypair is configured — gates real push delivery."""
        return bool(self.vapid_public_key and self.vapid_private_key)

    @property
    def is_production(self) -> bool:
        return self.environment.strip().lower() in {"production", "prod"}

    def insecure_defaults(self) -> list[str]:
        """Names of security-critical settings still left at their insecure dev default."""
        checks = {
            "session_secret": DEV_SESSION_SECRET,
            "google_client_id": DEV_GOOGLE_CLIENT_ID,
            "google_client_secret": DEV_GOOGLE_CLIENT_SECRET,
        }
        return [name for name, dev_default in checks.items() if getattr(self, name) == dev_default]


settings = Settings()
