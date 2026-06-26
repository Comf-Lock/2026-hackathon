"""LLM event enrichment (slice 4): Claude-Haiku topic + intent weighting.

Public surface: ``score_event`` (orchestrate + persist one event), ``is_enabled`` (graceful
on/off via API key), and the taxonomy constants the frontend colour map mirrors.
"""
from .score import is_enabled, score_event, score_text
from .taxonomy import INTENT_AXES, INTENT_SLUGS, TOPIC_FIELDS, TOPIC_SLUGS

__all__ = [
    "INTENT_AXES",
    "INTENT_SLUGS",
    "TOPIC_FIELDS",
    "TOPIC_SLUGS",
    "is_enabled",
    "score_event",
    "score_text",
]
