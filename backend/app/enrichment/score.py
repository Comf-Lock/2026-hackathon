"""Claude-Haiku event weighting (slice 4).

Estimates a topic mix + intent mix for an event from its text, using Claude Haiku with
structured output. The design separates three concerns so the expensive/non-deterministic
part is isolated and the rest is unit-testable without any network:

- ``text_hash`` / ``build_text`` — derive the cache key + the text we send.
- ``_call_llm`` — the only function that talks to Anthropic. Tests mock *this*; there is
  never a real API call in the test suite.
- ``_normalize`` — pure: takes the raw LLM dict, drops off-taxonomy / near-zero entries,
  and renormalises each axis to sum to 100. Deterministic, fully tested.
- ``score_event`` — orchestrates: thin-text guard, hash cache, call, normalise, persist.

Graceful degradation: with no ``ANTHROPIC_API_KEY`` set, ``is_enabled()`` is False and the
whole step is skipped — no crash, events keep their empty weights and the frontend shows its
placeholder bar.
"""
from __future__ import annotations

import hashlib
import json
import logging

from ..config import settings
from .taxonomy import INTENT_SLUGS, TOPIC_SLUGS

logger = logging.getLogger(__name__)

# Descriptions below ~120 chars carry too little signal to weight reliably — skip them
# (the placeholder bar stays). Keeps spend off thin scrapes.
THIN_TEXT_MIN = 120

# An axis weight below this (after the LLM's own 0..100 estimate) is treated as noise and dropped.
NEAR_ZERO = 2.0

# Hosted-model id — newest Haiku. Structured outputs supported; no effort/thinking params.
DEFAULT_SCORE_MODEL = "claude-haiku-4-5"

_SYSTEM_PROMPT = (
    "You classify tech-event descriptions for an IT event radar in Mainfranken, Germany. "
    "Estimate two distributions from the event text:\n"
    "1. topics — how the event's content splits across the canonical IT fields. Only include "
    "fields the text actually supports; weights are rough percentages that should sum to ~100.\n"
    "2. intents — the event's character across four axes (deep technical content, recruiting/"
    "hiring, vendor/sales pitch, networking/community). Weights are rough percentages summing to ~100.\n"
    "Also give an overall confidence (0..1) in your read and one short evidence phrase quoting "
    "the text. Be conservative: if the text is vague, lower the confidence. Do not invent fields "
    "the text does not support."
)


def _output_schema() -> dict:
    """JSON schema for the structured output.

    Uses enum-constrained ``field``/``axis`` keys inside arrays rather than a dynamic-key object,
    because strict structured output requires ``additionalProperties: false`` and fixed keys.
    """
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["topics", "intents", "confidence", "evidence"],
        "properties": {
            "topics": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["field", "weight"],
                    "properties": {
                        "field": {"type": "string", "enum": list(TOPIC_SLUGS)},
                        "weight": {"type": "number"},
                    },
                },
            },
            "intents": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["axis", "weight"],
                    "properties": {
                        "axis": {"type": "string", "enum": list(INTENT_SLUGS)},
                        "weight": {"type": "number"},
                    },
                },
            },
            "confidence": {"type": "number"},
            "evidence": {"type": "string"},
        },
    }


def is_enabled() -> bool:
    """True when an API key is configured; otherwise scoring is skipped gracefully."""
    return bool(settings.anthropic_api_key)


def build_text(
    title: str,
    description: str | None,
    organizer: str | None,
    tags: list[str] | None,
) -> str:
    """Assemble the text we send to the model (and hash) from the weight-bearing fields."""
    parts = [title or ""]
    if description:
        parts.append(description)
    if organizer:
        parts.append(f"Veranstalter: {organizer}")
    if tags:
        parts.append("Tags: " + ", ".join(tags))
    return "\n".join(p for p in parts if p).strip()


def text_hash(text: str) -> str:
    """Stable cache key for a given input text — re-scoring only on text change."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _normalize(raw: dict) -> dict:
    """Pure: clean + renormalise the raw LLM output. No network, fully deterministic.

    - keeps only on-taxonomy slugs (defensive; the schema already constrains them)
    - drops negative / near-zero weights
    - renormalises each axis to sum to exactly 100 (rounded ints, remainder on the largest)
    - clamps confidence to 0..1, trims evidence
    """
    topic_weights = _normalize_axis(raw.get("topics"), "field", TOPIC_SLUGS)
    intent_weights = _normalize_axis(raw.get("intents"), "axis", INTENT_SLUGS)

    confidence = raw.get("confidence", 0.0)
    try:
        confidence = max(0.0, min(1.0, float(confidence)))
    except (TypeError, ValueError):
        confidence = 0.0

    evidence = raw.get("evidence") or ""
    if not isinstance(evidence, str):
        evidence = str(evidence)
    evidence = evidence.strip()[:280]

    return {
        "topic_weights": topic_weights,
        "intent_weights": intent_weights,
        "confidence": confidence,
        "evidence": evidence,
    }


def _normalize_axis(items: object, key: str, allowed: tuple[str, ...]) -> dict[str, int]:
    """Turn a ``[{key: slug, weight: n}, ...]`` list into a clean ``{slug: int}`` summing to 100."""
    if not isinstance(items, list):
        return {}

    collected: dict[str, float] = {}
    for item in items:
        if not isinstance(item, dict):
            continue
        slug = item.get(key)
        weight = item.get("weight")
        if slug not in allowed:
            continue
        try:
            weight = float(weight)
        except (TypeError, ValueError):
            continue
        if weight < NEAR_ZERO:
            continue
        # Last write wins if the model emitted a slug twice — sum instead, more robust.
        collected[slug] = collected.get(slug, 0.0) + weight

    total = sum(collected.values())
    if total <= 0:
        return {}

    # Scale to 100 and round; fix rounding drift by dumping the remainder on the largest entry.
    scaled = {slug: w / total * 100 for slug, w in collected.items()}
    rounded = {slug: int(round(w)) for slug, w in scaled.items()}
    drift = 100 - sum(rounded.values())
    if drift and rounded:
        biggest = max(rounded, key=lambda s: scaled[s])
        rounded[biggest] += drift
    # Drop anything that rounded down to 0.
    return {slug: w for slug, w in rounded.items() if w > 0}


def _call_llm(text: str) -> dict:
    """Call Claude Haiku with structured output and return the raw parsed dict.

    The ONLY function in this module that performs network I/O. Tests mock this.
    """
    import anthropic  # imported lazily so the package is optional when scoring is disabled

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    response = client.messages.create(
        model=settings.score_model,
        max_tokens=1024,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": text}],
        output_config={"format": {"type": "json_schema", "schema": _output_schema()}},
    )
    payload = next((b.text for b in response.content if b.type == "text"), None)
    if not payload:
        raise ValueError("LLM returned no text block")
    return json.loads(payload)


def score_text(text: str) -> dict:
    """Score a piece of text → normalised result. Raises on LLM/parse failure (caller isolates)."""
    return _normalize(_call_llm(text))
