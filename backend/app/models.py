"""Persistence models for Event Radar.

A User is created from the Google identity (google_sub is the stable key). Each user
has exactly one Profile holding their interests/expertise and home location + radius,
which later drives the "events near you" matching.
"""
from datetime import datetime, timezone

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(SQLModel, table=True):
    __tablename__ = "users"  # "user" is a reserved word in Postgres — avoid quoting headaches.

    id: int | None = Field(default=None, primary_key=True)
    google_sub: str = Field(index=True, unique=True)
    email: str
    display_name: str
    avatar_url: str | None = None
    created_at: datetime = Field(default_factory=_utcnow)


class Profile(SQLModel, table=True):
    __tablename__ = "profiles"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", unique=True, index=True)

    # Stored as JSON arrays — DB-agnostic and good enough for slice 1.
    interests: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    expertise: list[str] = Field(default_factory=list, sa_column=Column(JSON))

    home_label: str | None = None
    home_lat: float | None = None
    home_lng: float | None = None
    radius_km: int = 40
