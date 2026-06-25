"""Shared test fixtures: an isolated in-memory DB and a TestClient wired to it.

The app's get_session dependency is overridden to a throwaway SQLite session so tests never touch
the configured Postgres. TestClient is created without its context manager on purpose — that skips
the lifespan (which would init the real engine); the schema is created here instead.
"""
from __future__ import annotations

import os

# Force SQLite before any app import so the module-level engine never needs the Postgres driver.
os.environ.setdefault("DATABASE_URL", "sqlite://")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.db import get_session
from app.main import app
from app.models import Event  # noqa: F401  — register tables on metadata


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
