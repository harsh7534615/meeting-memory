"""
Gemini embedder — generates embeddings via text-embedding-004.

- Batches in groups of 20 (API rate limit safety)
- Retries with exponential backoff on 429 errors
"""
import asyncio
import logging
import time
from typing import Optional

import google.generativeai as genai

from app.config import settings

logger = logging.getLogger(__name__)

BATCH_SIZE = 20
MAX_RETRIES = 5
BASE_DELAY = 1.0  # seconds

_configured = False


def _ensure_configured():
    global _configured
    if not _configured and settings.gemini_api_key:
        genai.configure(api_key=settings.gemini_api_key)
        _configured = True


def embed_single(text: str) -> list[float]:
    """Embed a single text string. Returns a 768-dim vector."""
    _ensure_configured()
    result = genai.embed_content(
        model="models/gemini-embedding-001",
        content=text,
        task_type="retrieval_document",
        output_dimensionality=768,
    )
    return result["embedding"]


def embed_query(text: str) -> list[float]:
    """Embed a query string (uses retrieval_query task type)."""
    _ensure_configured()
    result = genai.embed_content(
        model="models/gemini-embedding-001",
        content=text,
        task_type="retrieval_query",
        output_dimensionality=768,
    )
    return result["embedding"]


def embed_batch(texts: list[str]) -> list[list[float]]:
    """
    Embed a batch of texts with rate limiting and retries.

    Splits into groups of BATCH_SIZE and retries on 429 errors.
    """
    _ensure_configured()
    all_embeddings = []

    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i : i + BATCH_SIZE]
        embeddings = _embed_with_retry(batch)
        all_embeddings.extend(embeddings)

    return all_embeddings


def _embed_with_retry(texts: list[str]) -> list[list[float]]:
    """Embed a batch with exponential backoff on rate limit errors."""
    for attempt in range(MAX_RETRIES):
        try:
            result = genai.embed_content(
                model="models/gemini-embedding-001",
                content=texts,
                task_type="retrieval_document",
                output_dimensionality=768,
            )
            return result["embedding"]
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "quota" in error_str.lower():
                delay = BASE_DELAY * (2 ** attempt)
                logger.warning(
                    f"Rate limited (attempt {attempt + 1}/{MAX_RETRIES}), "
                    f"retrying in {delay}s..."
                )
                time.sleep(delay)
            else:
                raise

    raise RuntimeError(f"Failed to embed after {MAX_RETRIES} retries")


def generate_summary(transcript_text: str) -> str:
    """Generate a 3-5 bullet point summary of a meeting transcript using Gemini."""
    _ensure_configured()
    model = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content(
        f"""Summarize this meeting transcript in 3-5 concise bullet points.
Focus on: key decisions made, action items assigned, and important topics discussed.
Format each bullet with a dash (-).

Transcript:
{transcript_text[:10000]}"""  # Limit input to ~10k chars for safety
    )
    return response.text
