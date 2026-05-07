from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import User, OAuthToken
from app.database.postgres import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


class UserSyncRequest(BaseModel):
    google_id: str
    email: str
    name: Optional[str] = None
    avatar_url: Optional[str] = None
    access_token: str
    refresh_token: Optional[str] = None
    expires_at: Optional[str] = None
    scope: Optional[str] = None


class UserProfile(BaseModel):
    id: str
    google_id: str
    email: str
    name: Optional[str]
    avatar_url: Optional[str]
    timezone: str
    digest_enabled: bool


@router.post("/sync")
async def sync_user(req: UserSyncRequest, db: AsyncSession = Depends(get_db)):
    """Called by NextAuth on sign-in. Creates or updates user + tokens."""
    # Find or create user
    result = await db.execute(select(User).where(User.google_id == req.google_id))
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            google_id=req.google_id,
            email=req.email,
            name=req.name,
            avatar_url=req.avatar_url,
        )
        db.add(user)
        await db.flush()
    else:
        user.name = req.name
        user.avatar_url = req.avatar_url
        user.email = req.email

    # Upsert OAuth token
    result = await db.execute(
        select(OAuthToken).where(OAuthToken.user_id == user.id)
    )
    token = result.scalar_one_or_none()

    expires_at = None
    if req.expires_at:
        expires_at = datetime.fromisoformat(req.expires_at.replace("Z", "+00:00"))

    if not token:
        token = OAuthToken(
            user_id=user.id,
            access_token=req.access_token,
            refresh_token=req.refresh_token,
            expires_at=expires_at,
            scope=req.scope,
        )
        db.add(token)
    else:
        token.access_token = req.access_token
        if req.refresh_token:
            token.refresh_token = req.refresh_token
        token.expires_at = expires_at
        token.scope = req.scope
        token.updated_at = datetime.utcnow()

    await db.commit()
    return {"status": "ok", "user_id": str(user.id)}


@router.get("/me", response_model=UserProfile)
async def get_me(google_id: str, db: AsyncSession = Depends(get_db)):
    """Return user profile by google_id. Called by frontend to validate session."""
    result = await db.execute(select(User).where(User.google_id == google_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserProfile(
        id=str(user.id),
        google_id=user.google_id,
        email=user.email,
        name=user.name,
        avatar_url=user.avatar_url,
        timezone=user.timezone or "UTC",
        digest_enabled=user.digest_enabled if user.digest_enabled is not None else True,
    )
