"""Profile endpoints — read/update the current user's interests, expertise, home + radius."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlmodel import Session, select

from .auth import get_current_user
from .db import get_session
from .geocode import geocode
from .models import Profile, User

router = APIRouter(prefix="/api/profile", tags=["profile"])


class ProfileIn(BaseModel):
    interests: list[str] = []
    expertise: list[str] = []
    home_label: str | None = None
    radius_km: int = 40


class ProfileOut(BaseModel):
    interests: list[str]
    expertise: list[str]
    home_label: str | None
    home_lat: float | None
    home_lng: float | None
    radius_km: int


def _get_or_create(session: Session, user: User) -> Profile:
    profile = session.exec(select(Profile).where(Profile.user_id == user.id)).first()
    if profile is None:
        profile = Profile(user_id=user.id)
        session.add(profile)
        session.commit()
        session.refresh(profile)
    return profile


@router.get("", response_model=ProfileOut)
def get_profile(
    user: User = Depends(get_current_user), session: Session = Depends(get_session)
):
    return _get_or_create(session, user)


@router.put("", response_model=ProfileOut)
async def put_profile(
    data: ProfileIn,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    profile = _get_or_create(session, user)
    profile.interests = data.interests
    profile.expertise = data.expertise
    profile.radius_km = data.radius_km

    if data.home_label:
        # Re-geocode only when the label actually changed.
        if data.home_label != profile.home_label:
            profile.home_label = data.home_label
            coords = await geocode(data.home_label)
            if coords:
                profile.home_lat, profile.home_lng = coords
            else:
                profile.home_lat = profile.home_lng = None
    else:
        profile.home_label = None
        profile.home_lat = profile.home_lng = None

    session.add(profile)
    session.commit()
    session.refresh(profile)
    return profile
