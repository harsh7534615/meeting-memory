"""
Transcript processing orchestrator.

Pipeline for one file:
1. Chunk the transcript (chunker.py)
2. Embed each chunk (embedder.py)
3. Store vectors in Pinecone with metadata
4. Store meeting record in Postgres
5. Store chunk records in Postgres
6. Generate meeting summary via Gemini
7. Store summary in Postgres
"""
import logging
import re
import uuid
from datetime import datetime, date, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Meeting, Chunk as ChunkModel
from app.database.pinecone import get_index
from app.services.chunker import chunk_transcript
from app.services.embedder import embed_batch, generate_summary

logger = logging.getLogger(__name__)


def _extract_meeting_date(file_name: str) -> date | None:
    """Try to extract a date from the file name like '2026-05-01'."""
    match = re.search(r"(\d{4}-\d{2}-\d{2})", file_name)
    if match:
        try:
            return date.fromisoformat(match.group(1))
        except ValueError:
            pass
    return date.today()


def _extract_participants(transcript: str) -> list[str]:
    """Extract unique speaker names from transcript."""
    from app.services.chunker import SPEAKER_TURN_PATTERN
    matches = SPEAKER_TURN_PATTERN.findall(transcript)
    speakers = list(dict.fromkeys(name.strip() for name, _ in matches))
    return speakers if speakers else ["Unknown"]


async def process_transcript(
    user_id: str,
    drive_file_id: str,
    file_name: str,
    content: str,
    db: AsyncSession,
) -> str:
    """
    Full processing pipeline for one transcript file.
    Returns the meeting_id.
    """
    logger.info(f"Processing transcript: {file_name} for user {user_id}")

    # Check idempotency
    result = await db.execute(
        select(Meeting).where(Meeting.drive_file_id == drive_file_id)
    )
    if result.scalar_one_or_none():
        logger.info(f"Already processed: {drive_file_id}")
        return ""

    # Step 1: Chunk
    chunks = chunk_transcript(content)
    if not chunks:
        logger.warning(f"No chunks produced from {file_name}")
        return ""

    logger.info(f"Produced {len(chunks)} chunks from {file_name}")

    # Step 2: Embed
    texts = [c.text for c in chunks]
    embeddings = embed_batch(texts)

    # Step 3: Create meeting record in Postgres
    meeting_date = _extract_meeting_date(file_name)
    participants = _extract_participants(content)

    meeting = Meeting(
        user_id=user_id,
        title=file_name.replace("Meet Transcript - ", "").replace(".docx", "").replace(".txt", "").strip(),
        meeting_date=meeting_date,
        drive_file_id=drive_file_id,
        participant_names=participants,
        processed_at=datetime.now(timezone.utc),
    )
    db.add(meeting)
    await db.flush()  # Get meeting.id

    meeting_id = str(meeting.id)

    # Step 4: Store in Pinecone + Postgres
    pinecone_vectors = []
    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        pinecone_id = f"{meeting_id}_{i}"

        pinecone_vectors.append({
            "id": pinecone_id,
            "values": embedding,
            "metadata": {
                "user_id": user_id,
                "meeting_id": meeting_id,
                "chunk_id": pinecone_id,
                "speaker": chunk.speaker,
                "timestamp": chunk.start_time,
                "text_preview": chunk.text[:200],
            },
        })

        chunk_record = ChunkModel(
            meeting_id=meeting.id,
            user_id=user_id,
            pinecone_id=pinecone_id,
            speaker=chunk.speaker,
            start_time=chunk.start_time,
            end_time=chunk.end_time,
            text_preview=chunk.text[:200],
            chunk_index=chunk.chunk_index,
        )
        db.add(chunk_record)

    # Upsert to Pinecone in batches of 100
    index = get_index()
    for i in range(0, len(pinecone_vectors), 100):
        batch = pinecone_vectors[i : i + 100]
        index.upsert(vectors=batch)

    logger.info(f"Stored {len(pinecone_vectors)} vectors in Pinecone")

    # Step 5: Generate summary
    try:
        summary = generate_summary(content)
        meeting.summary = summary
        logger.info(f"Generated summary for {file_name}")
    except Exception as e:
        logger.error(f"Failed to generate summary: {e}")
        meeting.summary = "Summary generation failed."

    await db.commit()
    logger.info(f"Pipeline complete for {file_name} — meeting_id={meeting_id}")

    return meeting_id
