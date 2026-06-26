"""Tests for the LLM weighting step (slice 4).

The only network boundary — ``score._call_llm`` — is always mocked here: the suite never makes a
real Anthropic call. Everything else (``_normalize``, the hash cache, the persisted Event shape)
is exercised for real.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.enrichment import score
from app.enrichment.taxonomy import INTENT_SLUGS, TOPIC_SLUGS
from app.models import Event

NOW = datetime.now(timezone.utc)

# A realistic raw LLM payload (pre-normalisation): weights need not sum to 100, and the off-taxonomy
# field / near-zero entry below must be dropped by _normalize.
RAW_OK = {
    "topics": [
        {"field": "data_ai", "weight": 60},
        {"field": "backend_cloud", "weight": 30},
        {"field": "career_recruiting", "weight": 1},  # near-zero → dropped
        {"field": "not_a_real_field", "weight": 50},  # off-taxonomy → dropped
    ],
    "intents": [
        {"axis": "deep_tech", "weight": 70},
        {"axis": "networking", "weight": 30},
    ],
    "confidence": 0.82,
    "evidence": "Hands-on PyTorch workshop with cloud deployment.",
}

LONG_TEXT = (
    "Hands-on Deep Learning workshop: we build and train a PyTorch model end to end, "
    "then deploy it to a managed Kubernetes cluster. Bring a laptop. Suitable for "
    "engineers with some Python experience. Networking afterwards."
)


def _mk(session, **kw) -> Event:
    defaults = dict(title="Event", start=NOW + timedelta(days=1), is_online=False, tags=[])
    defaults.update(kw)
    ev = Event(**defaults)
    session.add(ev)
    session.commit()
    session.refresh(ev)
    return ev


# --- _normalize (pure) ---------------------------------------------------------------------


def test_normalize_drops_offtaxonomy_and_nearzero_and_sums_to_100():
    result = score._normalize(RAW_OK)
    assert set(result["topic_weights"]) <= set(TOPIC_SLUGS)
    assert "not_a_real_field" not in result["topic_weights"]
    assert "career_recruiting" not in result["topic_weights"]  # near-zero dropped
    assert sum(result["topic_weights"].values()) == 100
    assert sum(result["intent_weights"].values()) == 100
    assert set(result["intent_weights"]) <= set(INTENT_SLUGS)


def test_normalize_clamps_confidence():
    assert score._normalize({**RAW_OK, "confidence": 5})["confidence"] == 1.0
    assert score._normalize({**RAW_OK, "confidence": -3})["confidence"] == 0.0
    assert score._normalize({**RAW_OK, "confidence": "junk"})["confidence"] == 0.0


def test_normalize_empty_axes_when_nothing_valid():
    result = score._normalize({"topics": [], "intents": "garbage", "confidence": 0.5})
    assert result["topic_weights"] == {}
    assert result["intent_weights"] == {}


# --- is_enabled ----------------------------------------------------------------------------


def test_is_enabled_reflects_api_key(monkeypatch):
    monkeypatch.setattr(score.settings, "anthropic_api_key", "")
    assert score.is_enabled() is False
    monkeypatch.setattr(score.settings, "anthropic_api_key", "sk-test")
    assert score.is_enabled() is True


# --- score_event (orchestration, _call_llm mocked) -----------------------------------------


@pytest.fixture
def enabled(monkeypatch):
    monkeypatch.setattr(score.settings, "anthropic_api_key", "sk-test")
    monkeypatch.setattr(score.settings, "score_model", "claude-haiku-4-5")


def test_score_event_disabled_is_graceful(session, monkeypatch):
    monkeypatch.setattr(score.settings, "anthropic_api_key", "")
    ev = _mk(session, description=LONG_TEXT)
    assert score.score_event(session, ev) == "skipped:disabled"
    assert ev.topic_weights == {}


def test_score_event_thin_text_skipped(session, enabled, monkeypatch):
    called = {"n": 0}
    monkeypatch.setattr(score, "_call_llm", lambda text: called.__setitem__("n", called["n"] + 1) or RAW_OK)
    ev = _mk(session, title="x", description="short")
    assert score.score_event(session, ev) == "skipped:thin"
    assert called["n"] == 0  # never reached the model


def test_score_event_persists_weights(session, enabled, monkeypatch):
    monkeypatch.setattr(score, "_call_llm", lambda text: RAW_OK)
    ev = _mk(session, title="DL Workshop", description=LONG_TEXT)
    assert score.score_event(session, ev) == "scored"
    session.refresh(ev)
    assert sum(ev.topic_weights.values()) == 100
    assert sum(ev.intent_weights.values()) == 100
    assert ev.score_confidence == pytest.approx(0.82)
    assert ev.score_model == "claude-haiku-4-5"
    assert ev.scored_text_hash


def test_score_event_caches_on_unchanged_text(session, enabled, monkeypatch):
    calls = {"n": 0}

    def _fake(text):
        calls["n"] += 1
        return RAW_OK

    monkeypatch.setattr(score, "_call_llm", _fake)
    ev = _mk(session, title="DL Workshop", description=LONG_TEXT)
    assert score.score_event(session, ev) == "scored"
    assert score.score_event(session, ev) == "skipped:cached"
    assert calls["n"] == 1  # second run short-circuited, no second model call


def test_score_event_rescore_on_text_change(session, enabled, monkeypatch):
    monkeypatch.setattr(score, "_call_llm", lambda text: RAW_OK)
    ev = _mk(session, title="DL Workshop", description=LONG_TEXT)
    score.score_event(session, ev)
    first_hash = ev.scored_text_hash
    ev.description = LONG_TEXT + " Updated agenda with a security deep-dive session and CTF."
    session.add(ev)
    session.commit()
    assert score.score_event(session, ev) == "scored"
    assert ev.scored_text_hash != first_hash


def test_score_event_error_is_isolated(session, enabled, monkeypatch):
    def _boom(text):
        raise RuntimeError("model exploded")

    monkeypatch.setattr(score, "_call_llm", _boom)
    ev = _mk(session, title="DL Workshop", description=LONG_TEXT)
    assert score.score_event(session, ev) == "error"
    assert ev.topic_weights == {}  # nothing persisted on failure
