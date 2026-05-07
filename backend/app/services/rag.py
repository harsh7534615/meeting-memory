"""
RAG query pipeline — retrieval-augmented generation over meeting transcripts.

Pipeline:
1. Embed user question (Gemini text-embedding-004)
2. Query Pinecone top_k=10, filter by user_id
3. Confidence gate — if best score < 0.70, return early
4. Re-rank via Gemini (score 1-10), keep top 4
5. Fetch full metadata from Postgres
6. Build grounded prompt with [SOURCE N] tags
7. Generate answer via Gemini 1.5 Flash
8. Parse citations, attach meeting metadata
"""
import json
import logging
import re
from dataclasses import dataclass, field
from typing import Optional

import google.generativeai as genai
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database.models import Chunk, Meeting
from app.database.pinecone import get_index
from app.services.embedder import embed_query

logger = logging.getLogger(__name__)

CONFIDENCE_THRESHOLD = 0.70


@dataclass
class Citation:
    source_index: int
    meeting_title: str
    meeting_date: str
    speaker: str
    timestamp: str
    text_preview: str


@dataclass
class QueryResponse:
    answer: str
    citations: list[Citation] = field(default_factory=list)
    confidence: float = 0.0


GROUNDED_PROMPT_TEMPLATE = """Answer the user's question ONLY using the provided sources.
Cite each claim with [SOURCE N] where N is the source number.
If the sources do not contain enough information to answer confidently, say so explicitly.
Do not invent details.

Sources:
{context}

Question: {question}

Answer:"""


RERANK_PROMPT_TEMPLATE = """Given the question and a list of text passages, score each passage from 1-10 for relevance to answering the question.
Return ONLY a JSON array of scores in the same order as the passages, e.g. [8, 3, 7, ...].

Question: {question}

Passages:
{passages}

Scores (JSON array only):"""


def _build_context_string(chunks_with_meta: list[dict]) -> str:
    """Format chunks as [SOURCE N] blocks for the grounded prompt."""
    parts = []
    for i, item in enumerate(chunks_with_meta, 1):
        parts.append(
            f"[SOURCE {i}]\n"
            f"Meeting: {item['meeting_title']} ({item['meeting_date']})\n"
            f"Speaker: {item['speaker']} at {item['timestamp']}\n"
            f"Content: {item['text']}\n"
        )
    return "\n".join(parts)


def _extract_citations(answer: str, chunks_with_meta: list[dict]) -> list[Citation]:
    """Parse [SOURCE N] references from the answer and map to metadata."""
    citations = []
    seen = set()
    for match in re.finditer(r"\[SOURCE\s*(\d+)\]", answer):
        idx = int(match.group(1))
        if idx < 1 or idx > len(chunks_with_meta) or idx in seen:
            continue
        seen.add(idx)
        item = chunks_with_meta[idx - 1]
        citations.append(Citation(
            source_index=idx,
            meeting_title=item["meeting_title"],
            meeting_date=item["meeting_date"],
            speaker=item["speaker"],
            timestamp=item["timestamp"],
            text_preview=item["text"][:200],
        ))
    return citations


def _clean_answer(answer: str) -> str:
    """Clean up the generated answer."""
    return answer.strip()


async def _rerank_chunks(
    question: str, chunks: list[dict]
) -> list[tuple[dict, float]]:
    """Re-rank chunks using Gemini. Returns (chunk, score) sorted by score desc."""
    if not chunks:
        return []

    passages = "\n\n".join(
        f"Passage {i+1}: {c['text'][:500]}" for i, c in enumerate(chunks)
    )

    prompt = RERANK_PROMPT_TEMPLATE.format(question=question, passages=passages)

    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        text = response.text.strip()

        # Extract JSON array from response
        json_match = re.search(r"\[[\d,\s]+\]", text)
        if json_match:
            scores = json.loads(json_match.group())
        else:
            # Fallback: use Pinecone scores as-is
            logger.warning("Failed to parse rerank scores, using original order")
            return [(c, 10 - i) for i, c in enumerate(chunks)]

        # Pair chunks with scores
        scored = []
        for i, chunk in enumerate(chunks):
            score = scores[i] if i < len(scores) else 0
            scored.append((chunk, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored

    except Exception as e:
        logger.error(f"Reranking failed: {e}, using original order")
        return [(c, 10 - i) for i, c in enumerate(chunks)]


async def _fetch_chunk_metadata(
    pinecone_ids: list[str], db: AsyncSession
) -> dict[str, dict]:
    """Fetch chunk + meeting metadata from Postgres by Pinecone IDs."""
    result = await db.execute(
        select(Chunk, Meeting)
        .join(Meeting, Chunk.meeting_id == Meeting.id)
        .where(Chunk.pinecone_id.in_(pinecone_ids))
    )
    rows = result.all()

    meta = {}
    for chunk, meeting in rows:
        meta[chunk.pinecone_id] = {
            "meeting_title": meeting.title or "Untitled Meeting",
            "meeting_date": str(meeting.meeting_date) if meeting.meeting_date else "Unknown",
            "speaker": chunk.speaker or "Unknown",
            "timestamp": chunk.start_time or "00:00:00",
            "text": chunk.text_preview or "",
        }
    return meta


async def query(
    user_question: str,
    user_id: str,
    db: AsyncSession,
    filters: Optional[dict] = None,
) -> QueryResponse:
    """
    Main RAG query pipeline.

    Args:
        user_question: Natural language question from the user
        user_id: The authenticated user's ID
        db: Database session
        filters: Optional dict with date_from, date_to, speaker
    """
    # Step 1: Embed the question
    question_vector = embed_query(user_question)

    # Step 2: Build Pinecone filter
    pinecone_filter = {"user_id": user_id}
    # Note: date/speaker filters are applied post-retrieval since Pinecone
    # metadata filtering is limited. We fetch more and filter in Python.

    # Query Pinecone
    index = get_index()
    results = index.query(
        vector=question_vector,
        top_k=10,
        filter=pinecone_filter,
        include_metadata=True,
    )

    matches = results.get("matches", [])

    # Step 3: Confidence gate
    if not matches or matches[0]["score"] < CONFIDENCE_THRESHOLD:
        return QueryResponse(
            answer="I couldn't find a clear discussion about this in your meetings.",
            citations=[],
            confidence=matches[0]["score"] if matches else 0.0,
        )

    # Fetch metadata from Postgres
    pinecone_ids = [m["id"] for m in matches]
    db_meta = await _fetch_chunk_metadata(pinecone_ids, db)

    # Build chunk dicts with full text from metadata
    chunks_with_meta = []
    for m in matches:
        pid = m["id"]
        meta = db_meta.get(pid, {})
        if not meta:
            # Fallback to Pinecone metadata
            meta = {
                "meeting_title": "Unknown Meeting",
                "meeting_date": "Unknown",
                "speaker": m["metadata"].get("speaker", "Unknown"),
                "timestamp": m["metadata"].get("timestamp", "00:00:00"),
                "text": m["metadata"].get("text_preview", ""),
            }
        chunks_with_meta.append(meta)

    # Apply post-retrieval filters
    if filters:
        chunks_with_meta = _apply_filters(chunks_with_meta, filters)

    if not chunks_with_meta:
        return QueryResponse(
            answer="I couldn't find a clear discussion about this in your meetings with the given filters.",
            citations=[],
            confidence=0.0,
        )

    # Step 4: Re-rank, keep top 4
    reranked = await _rerank_chunks(user_question, chunks_with_meta)
    top_chunks = [chunk for chunk, score in reranked[:4]]

    # Step 5: Build grounded prompt
    context = _build_context_string(top_chunks)
    prompt = GROUNDED_PROMPT_TEMPLATE.format(
        context=context, question=user_question
    )

    # Step 6: Generate answer
    model = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content(prompt)
    raw_answer = response.text

    # Step 7: Parse citations
    citations = _extract_citations(raw_answer, top_chunks)

    return QueryResponse(
        answer=_clean_answer(raw_answer),
        citations=citations,
        confidence=matches[0]["score"],
    )


def _apply_filters(chunks: list[dict], filters: dict) -> list[dict]:
    """Apply date range and speaker filters to chunks."""
    filtered = chunks

    if filters.get("date_from"):
        filtered = [c for c in filtered if c["meeting_date"] >= filters["date_from"]]

    if filters.get("date_to"):
        filtered = [c for c in filtered if c["meeting_date"] <= filters["date_to"]]

    if filters.get("speaker"):
        speaker_lower = filters["speaker"].lower()
        filtered = [c for c in filtered if speaker_lower in c["speaker"].lower()]

    return filtered
