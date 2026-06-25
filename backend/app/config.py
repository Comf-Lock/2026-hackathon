"""Settings for the Event Radar API — loaded from environment / .env.

Google OAuth credentials default to placeholders so the whole app builds and runs
without a real client; Lars fills in the real values in .env when login is tested.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database — local default points at the docker-compose postgres on localhost.
    # Inside docker-compose this is overridden to host "db".
    database_url: str = "postgresql+psycopg://eventradar:eventradar@localhost:5432/eventradar"

    # Signed session cookie (httpOnly) — change in production.
    session_secret: str = "dev-insecure-session-secret-change-me"

    # Google OAuth — placeholders until Lars creates the OAuth client.
    google_client_id: str = "PLACEHOLDER_GOOGLE_CLIENT_ID"
    google_client_secret: str = "PLACEHOLDER_GOOGLE_CLIENT_SECRET"
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


settings = Settings()
