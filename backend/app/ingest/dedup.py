"""Cross-source dedup fingerprint (slice 5 v1).

Pure, deterministic, ML-free: the same real-world event listed on two sources (Meetup *and*
Eventbrite) must hash to the *same* fingerprint so the ingestion core can merge them into one
canonical Event with several EventSource rows. Precision over recall — two near-but-different
events (same title, different day) must stay apart, so the day-granular start date is part of the
key. Embeddings/fuzzy matching are explicitly out of scope for v1.

The fingerprint = sha256(normalized_title | start.date() | location), where location is the
normalized city or the literal "online". Keep this a pure function: it is unit-tested directly.
"""
from __future__ import annotations

import hashlib
import unicodedata
from datetime import datetime

from .types import RawEventRecord

# Generic German/English filler words stripped from titles before fingerprinting, so
# "Die KI-Konferenz" and "KI Konferenz" collapse to the same key. Intentionally small and
# generic — only words that carry no event identity.
_FILLER = frozenset(
    {
        "der", "die", "das", "den", "dem", "des", "ein", "eine", "einen", "einem", "einer",
        "und", "oder", "im", "in", "am", "an", "auf", "bei", "mit", "zum", "zur", "fuer", "fur",
        "the", "a", "an", "and", "or", "of", "for", "at", "on", "in", "to", "with",
    }
)


def _strip_accents(text: str) -> str:
    """Fold accents/umlauts to ASCII (ä→a, é→e) via NFKD decomposition, dropping combining marks."""
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def normalize_title(title: str) -> str:
    """Normalize an event title to a stable comparison key.

    lowercase → strip accents → non-alphanumerics to spaces → drop generic filler words →
    collapse whitespace. The result is what goes into the fingerprint, never shown to users.
    """
    folded = _strip_accents((title or "").lower())
    cleaned = "".join(ch if ch.isalnum() else " " for ch in folded)
    tokens = [t for t in cleaned.split() if t and t not in _FILLER]
    return " ".join(tokens)


def normalize_location(city: str | None, is_online: bool) -> str:
    """Normalize the location component: "online" for online events, else the normalized city.

    Returns "" when an in-person event has no city — an unknown location must not be treated as
    equal to another unknown one *across different events*; the title+date still separate them.
    """
    if is_online:
        return "online"
    if not city:
        return ""
    folded = _strip_accents(city.lower())
    cleaned = "".join(ch if ch.isalnum() else " " for ch in folded)
    return " ".join(cleaned.split())


def event_fingerprint(title: str, start: datetime, city: str | None, is_online: bool) -> str:
    """Deterministic cross-source fingerprint: sha256(normtitle | start-date | location), 24 hex.

    Day granularity on the start (not the exact timestamp) so two sources that disagree on the
    minute still merge; the date is the strong discriminator that keeps a weekly series apart.
    """
    basis = f"{normalize_title(title)}|{start.date().isoformat()}|{normalize_location(city, is_online)}"
    return "fp:" + hashlib.sha256(basis.encode("utf-8")).hexdigest()[:24]


def record_fingerprint(record: RawEventRecord) -> str:
    """Fingerprint for an adapter record — the value stored on Event.dedup_key at ingest time."""
    return event_fingerprint(record.title, record.start, record.city, record.is_online)
