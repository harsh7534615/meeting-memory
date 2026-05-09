import logging
import sys

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import User
from app.database.postgres import get_db
from app.routers import auth, meetings, query, webhooks

# --- Structured logging ---
logging.basicConfig(
    level=logging.INFO,
    format='{"time":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","message":"%(message)s"}',
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("meeting_memory")

# --- Rate limiter ---
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="Meeting Memory OS",
    description="Query your entire meeting history in natural language",
    version="0.1.0",
)

app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "Too many requests. Please try again in a minute."},
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://meeting-memory.vercel.app",
        "https://meeting-memory-kggu.onrender.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(meetings.router)
app.include_router(query.router)
app.include_router(webhooks.router)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/digest/preview")
async def digest_preview(google_id: str, db: AsyncSession = Depends(get_db)):
    """Preview this week's digest for a user."""
    from app.services.digest import generate_digest

    user_result = await db.execute(select(User).where(User.google_id == google_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    digest = await generate_digest(str(user.id), db)
    if not digest:
        return {"message": "No meetings this week", "digest": None}

    return {
        "subject": digest["subject"],
        "body": digest["body_text"],
        "meetings_count": digest["meetings_count"],
    }
