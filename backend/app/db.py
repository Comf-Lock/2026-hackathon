"""Database engine + session helpers.

Slice 1 uses SQLModel.metadata.create_all on startup instead of Alembic migrations:
the schema is still small and local-only, so plain create_all keeps the dev loop fast.
Alembic is introduced once the schema stabilises (tracked in the slice plan).
"""
from collections.abc import Iterator

from sqlmodel import Session, SQLModel, create_engine

from .config import settings

engine = create_engine(settings.database_url, echo=False)


def init_db() -> None:
    # Import models so they are registered on SQLModel.metadata before create_all.
    from . import models  # noqa: F401

    SQLModel.metadata.create_all(engine)


def get_session() -> Iterator[Session]:
    with Session(engine) as session:
        yield session
