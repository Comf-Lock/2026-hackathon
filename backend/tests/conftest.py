"""Shared test fixtures.

Two concerns combined:
- ``fixture_text``: read captured HTML/JSON fixtures so adapter-parse tests never touch the live
  network (sources are bot-shy and change over time). Fixtures captured 2026-06-25.
- ``session`` / ``client``: an isolated in-memory SQLite DB and a TestClient wired to it, so API
  tests never touch the configured Postgres. TestClient is created without its context manager on
  purpose — that skips the lifespan (which would init the real engine); schema is created here.
"""
from __future__ import annotations

import os

# Force SQLite before any app import so the module-level engine never needs the Postgres driver.
os.environ.setdefault("DATABASE_URL", "sqlite://")

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.db import get_session
from app.main import app
from app.models import Event  # noqa: F401  — register tables on metadata

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixture_text():
    def _read(name: str) -> str:
        return (FIXTURES / name).read_text(encoding="utf-8")

    return _read


@pytest.fixture
def session():
    # StaticPool keeps a single shared connection so the in-memory schema is visible from the
    # TestClient's request thread too (a fresh connection would see an empty database).
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as s:
        yield s


@pytest.fixture
def client(session):
    app.dependency_overrides[get_session] = lambda: session
    yield TestClient(app)
    app.dependency_overrides.clear()
