"""Meetings endpoints — list and detail views."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Meeting, Chunk, User
from app.database.postgres import get_db

router = APIRouter(prefix="/meetings", tags=["meetings"])


class MeetingResponse(BaseModel):
    id: str
    title: Optional[str]
    meeting_date: Optional[str]
    duration_minutes: Optional[int]
    summary: Optional[str]
    participant_names: list[str]
    processed_at: Optional[str]


class ChunkResponse(BaseModel):
    id: str
    speaker: Optional[str]
    start_time: Optional[str]
    end_time: Optional[str]
    text_preview: Optional[str]
    chunk_index: Optional[int]


class MeetingDetailResponse(MeetingResponse):
    chunks: list[ChunkResponse]


@router.get("", response_model=list[MeetingResponse])
async def list_meetings(google_id: str, db: AsyncSession = Depends(get_db)):
    """List all meetings for a user, ordered by date descending."""
    user_result = await db.execute(select(User).where(User.google_id == google_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    result = await db.execute(
        select(Meeting)
        .where(Meeting.user_id == user.id)
        .order_by(Meeting.meeting_date.desc())
    )
    meetings = result.scalars().all()

    return [
        MeetingResponse(
            id=str(m.id),
            title=m.title,
            meeting_date=str(m.meeting_date) if m.meeting_date else None,
            duration_minutes=m.duration_minutes,
            summary=m.summary,
            participant_names=m.participant_names or [],
            processed_at=str(m.processed_at) if m.processed_at else None,
        )
        for m in meetings
    ]


@router.get("/{meeting_id}", response_model=MeetingDetailResponse)
async def get_meeting(meeting_id: str, db: AsyncSession = Depends(get_db)):
    """Get meeting detail with chunks."""
    result = await db.execute(select(Meeting).where(Meeting.id == meeting_id))
    meeting = result.scalar_one_or_none()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    chunks_result = await db.execute(
        select(Chunk)
        .where(Chunk.meeting_id == meeting.id)
        .order_by(Chunk.chunk_index)
    )
    chunks = chunks_result.scalars().all()

    return MeetingDetailResponse(
        id=str(meeting.id),
        title=meeting.title,
        meeting_date=str(meeting.meeting_date) if meeting.meeting_date else None,
        duration_minutes=meeting.duration_minutes,
        summary=meeting.summary,
        participant_names=meeting.participant_names or [],
        processed_at=str(meeting.processed_at) if meeting.processed_at else None,
        chunks=[
            ChunkResponse(
                id=str(c.id),
                speaker=c.speaker,
                start_time=c.start_time,
                end_time=c.end_time,
                text_preview=c.text_preview,
                chunk_index=c.chunk_index,
            )
            for c in chunks
        ],
    )
