"""Adapter contract types: what every source adapter produces, and the scope it searches.

RawEventRecord is the single normalized shape the ingestion core understands — adapters map
their source's raw fields onto it (provenance + canonical event fields). It is deliberately a
plain Pydantic model, decoupled from the SQLModel tables in app.models, so adapters never depend
on the DB layer. GeoScope is the configurable search window (default: Mainfranken).
"""
from __future__ import annotations

import hashlib
from datetime import datetime

from pydantic import BaseModel, Field


class GeoScope(BaseModel):
    """The geographic + topical window an adapter searches.

    Default is fixed to Mainfranken (Würzburg centre), but every field is configurable so the
    scope can widen without code changes — the goal is later going global. Used by adapters that
    accept a search radius and by the core keyword/geo filter.
    """

    center_label: str = "Würzburg"
    center_lat: float = 49.7913
    center_lng: float = 9.9534
    # 75 km from Würzburg covers all of Mainfranken incl. the Bayerischer Untermain
    # (Aschaffenburg ~61 km, Miltenberg ~50 km) while still excluding Nürnberg (~90 km)
    # and Frankfurt (~85 km).
    radius_km: int = 75

    # Postal-code prefixes that count as in-scope when a record carries a postal code but no
    # coordinates. 97 = Unterfranken core (Würzburg/Schweinfurt/Kitzingen/…), 63 = Bayerischer
    # Untermain (Aschaffenburg/Miltenberg). A coarse structural fallback — distance wins when
    # coordinates exist.
    postal_prefixes: list[str] = Field(default_factory=lambda: ["97", "63"])

    # Cities that count as "in scope" for adapters/filters that only expose place names.
    cities: list[str] = Field(
        default_factory=lambda: [
            "Würzburg", "Schweinfurt", "Aschaffenburg", "Kitzingen", "Bad Kissingen",
            "Karlstadt", "Marktheidenfeld", "Haßfurt", "Bad Neustadt", "Miltenberg",
            "Lohr", "Ochsenfurt", "Gerolzhofen", "Volkach", "Mainfranken", "Unterfranken",
        ]
    )

    # Title keywords that mark an event as IT/tech relevant (broad calendars need this).
    keywords: list[str] = Field(
        default_factory=lambda: [
            "ki", "ai", "künstliche intelligenz", "machine learning", "ml", "data",
            "daten", "hackathon", "barcamp", "web", "digital", "cyber", "security",
            "dev", "developer", "software", "coding", "code", "startup", "start-up",
            "tech", "it-", "cloud", "devops", "python", "javascript", "agile",
        ]
    )


class RawEventRecord(BaseModel):
    """One event as produced by a source adapter — provenance + canonical fields.

    Fields without a value stay None; slice-4 enrichment fills missing geo. The ingestion core
    turns this into an Event + EventSource row, upserting on (source_adapter, external_id).
    """

    # --- Provenance ---
    source_adapter: str
    external_id: str | None = None  # None → derived via stable_external_id() at ingest time
    source_url: str
    fetched_at: datetime | None = None  # None → stamped to now() by the core
    raw_payload: dict = Field(default_factory=dict)
    origin_type: str = "scrape"  # scrape | feed | api | organizer | crowd
    trust_tier: int = 3  # 1=high … 3=low

    # --- Canonical event fields ---
    title: str
    description: str | None = None
    start: datetime
    end: datetime | None = None
    is_online: bool = False

    venue_name: str | None = None
    address: str | None = None
    city: str | None = None
    postal_code: str | None = None
    lat: float | None = None
    lng: float | None = None

    organizer: str | None = None
    tags: list[str] = Field(default_factory=list)
    url: str | None = None
    image_url: str | None = None
    price: str | None = None
    language: str | None = None

    def stable_external_id(self) -> str:
        """Return external_id, or a deterministic fallback when the source has no stable id.

        Fallback = sha256(source_url | title | start) — same event on a re-run hashes the same,
        so the upsert key stays stable and re-runs never duplicate.
        """
        if self.external_id:
            return self.external_id
        basis = f"{self.source_url}|{self.title}|{self.start.isoformat()}"
        return "sha256:" + hashlib.sha256(basis.encode("utf-8")).hexdigest()[:32]
