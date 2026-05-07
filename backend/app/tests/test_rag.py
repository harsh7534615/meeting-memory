"""Tests for RAG pipeline internals."""
from app.services.rag import (
    _build_context_string,
    _extract_citations,
    _clean_answer,
    _apply_filters,
    CONFIDENCE_THRESHOLD,
)


SAMPLE_CHUNKS = [
    {
        "meeting_title": "Sprint Planning",
        "meeting_date": "2026-03-15",
        "speaker": "Alice",
        "timestamp": "00:05:30",
        "text": "We decided to use JWT tokens for the auth system. Bob will implement it by Friday.",
    },
    {
        "meeting_title": "Design Review",
        "meeting_date": "2026-03-20",
        "speaker": "Bob",
        "timestamp": "00:12:00",
        "text": "The auth system is now using Google OAuth with NextAuth.js. All tests pass.",
    },
    {
        "meeting_title": "All Hands",
        "meeting_date": "2026-04-01",
        "speaker": "Carol",
        "timestamp": "00:30:00",
        "text": "Q2 budget approved. We have $50k for infrastructure upgrades.",
    },
]


def test_build_context_string():
    """Context string should contain SOURCE tags and metadata."""
    ctx = _build_context_string(SAMPLE_CHUNKS)
    assert "[SOURCE 1]" in ctx
    assert "[SOURCE 2]" in ctx
    assert "[SOURCE 3]" in ctx
    assert "Sprint Planning" in ctx
    assert "Alice" in ctx


def test_extract_citations_single():
    """Should extract a single citation from answer."""
    answer = "Based on the discussion [SOURCE 1], JWT tokens were chosen."
    citations = _extract_citations(answer, SAMPLE_CHUNKS)
    assert len(citations) == 1
    assert citations[0].source_index == 1
    assert citations[0].meeting_title == "Sprint Planning"


def test_extract_citations_multiple():
    """Should extract multiple citations."""
    answer = "Auth was discussed in [SOURCE 1] and [SOURCE 2]."
    citations = _extract_citations(answer, SAMPLE_CHUNKS)
    assert len(citations) == 2


def test_extract_citations_deduplicates():
    """Should not duplicate citations for same source."""
    answer = "See [SOURCE 1] and also [SOURCE 1] again."
    citations = _extract_citations(answer, SAMPLE_CHUNKS)
    assert len(citations) == 1


def test_extract_citations_ignores_invalid():
    """Should ignore SOURCE references beyond available chunks."""
    answer = "See [SOURCE 99]."
    citations = _extract_citations(answer, SAMPLE_CHUNKS)
    assert len(citations) == 0


def test_extract_citations_none():
    """Should return empty list when no citations in answer."""
    answer = "No specific source referenced here."
    citations = _extract_citations(answer, SAMPLE_CHUNKS)
    assert len(citations) == 0


def test_clean_answer():
    """Should strip whitespace."""
    assert _clean_answer("  Hello world  ") == "Hello world"


def test_confidence_threshold():
    """Threshold should be 0.70."""
    assert CONFIDENCE_THRESHOLD == 0.70


# --- Filter tests ---

def test_filter_by_date_from():
    filtered = _apply_filters(SAMPLE_CHUNKS, {"date_from": "2026-03-20"})
    assert len(filtered) == 2
    assert all(c["meeting_date"] >= "2026-03-20" for c in filtered)


def test_filter_by_date_to():
    filtered = _apply_filters(SAMPLE_CHUNKS, {"date_to": "2026-03-20"})
    assert len(filtered) == 2
    assert all(c["meeting_date"] <= "2026-03-20" for c in filtered)


def test_filter_by_date_range():
    filtered = _apply_filters(SAMPLE_CHUNKS, {"date_from": "2026-03-16", "date_to": "2026-03-31"})
    assert len(filtered) == 1
    assert filtered[0]["speaker"] == "Bob"


def test_filter_by_speaker():
    filtered = _apply_filters(SAMPLE_CHUNKS, {"speaker": "carol"})
    assert len(filtered) == 1
    assert filtered[0]["speaker"] == "Carol"


def test_filter_empty_returns_all():
    filtered = _apply_filters(SAMPLE_CHUNKS, {})
    assert len(filtered) == 3
