"""Query endpoint — accepts natural language questions about meetings."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import User
from app.database.postgres import get_db
from app.services.rag import query as rag_query

router = APIRouter(tags=["query"])
limiter = Limiter(key_func=get_remote_address)


class QueryFilters(BaseModel):
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    speaker: Optional[str] = None


class QueryRequest(BaseModel):
    question: str
    user_id: str
    filters: Optional[QueryFilters] = None


class CitationResponse(BaseModel):
    source_index: int
    meeting_title: str
    meeting_date: str
    speaker: str
    timestamp: str
    text_preview: str


class QueryResponseModel(BaseModel):
    answer: str
    citations: list[CitationResponse]
    confidence: float


@router.post("/query", response_model=QueryResponseModel)
@limiter.limit("10/minute")
async def query_meetings(
    request: Request,
    req: QueryRequest,
    db: AsyncSession = Depends(get_db),
):
    """Submit a natural language question against meeting history."""
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    # Resolve google_id → postgres user_id
    user_result = await db.execute(select(User).where(User.google_id == req.user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    filters = None
    if req.filters:
        filters = req.filters.model_dump(exclude_none=True)

    result = await rag_query(
        user_question=req.question,
        user_id=str(user.id),
        db=db,
        filters=filters,
    )

    return QueryResponseModel(
        answer=result.answer,
        citations=[
            CitationResponse(
                source_index=c.source_index,
                meeting_title=c.meeting_title,
                meeting_date=c.meeting_date,
                speaker=c.speaker,
                timestamp=c.timestamp,
                text_preview=c.text_preview,
            )
            for c in result.citations
        ],
        confidence=result.confidence,
    )
