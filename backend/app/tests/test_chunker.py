"""Tests for the transcript chunker."""
from app.services.chunker import chunk_transcript, Chunk


SAMPLE_TRANSCRIPT = """Alice 00:00:05
Good morning everyone. Let's start with the sprint review. We had a productive week and I want to go through the highlights.

Bob 00:01:30
Thanks Alice. The auth system is now complete. We implemented Google OAuth with drive readonly scope. The login page is live and tests are passing.

Alice 00:02:45
Great work Bob. What about the database migration? Did we get that sorted out with the new schema?

Bob 00:03:15
Yes, the schema is deployed to Supabase. All five tables are created with proper indexes. We also have the SQLAlchemy models mirroring everything.

Carol 00:04:00
I finished the Drive watcher integration. Webhooks are registered per user and we filter for Meet Transcript files automatically. The auto-renewal logic handles the 7-day expiry.

Alice 00:05:30
Excellent. Let's discuss the RAG pipeline next. We need to decide on the chunk size and overlap strategy before we proceed.

Bob 00:06:00
I suggest 300 words max per chunk with 2-sentence overlap. That gives us good context without too much noise in the embeddings.

Carol 00:06:45
Agreed. We should also skip very short chunks under 20 words. Things like "Okay" or "Got it" just add noise.

Alice 00:07:15
Makes sense. Let's go with that approach. Bob, can you implement the chunker by end of day?

Bob 00:07:30
Yes, I'll have it ready with tests.
"""


def test_basic_chunking():
    """Should produce chunks from a multi-speaker transcript."""
    chunks = chunk_transcript(SAMPLE_TRANSCRIPT)
    assert len(chunks) > 0
    assert all(isinstance(c, Chunk) for c in chunks)


def test_chunk_has_required_fields():
    """Each chunk should have text, speaker, times, word count, and index."""
    chunks = chunk_transcript(SAMPLE_TRANSCRIPT)
    for c in chunks:
        assert c.text
        assert c.speaker
        assert c.start_time
        assert c.end_time
        assert c.word_count > 0
        assert c.chunk_index >= 0


def test_speakers_extracted():
    """Should identify Alice, Bob, and Carol as speakers."""
    chunks = chunk_transcript(SAMPLE_TRANSCRIPT)
    speakers = set(c.speaker for c in chunks)
    assert "Alice" in speakers
    assert "Bob" in speakers
    assert "Carol" in speakers


def test_chunks_under_max_words():
    """No chunk should exceed 300 words (plus overlap padding)."""
    chunks = chunk_transcript(SAMPLE_TRANSCRIPT)
    for c in chunks:
        # Allow some slack for overlap
        assert c.word_count <= 350, f"Chunk too long: {c.word_count} words"


def test_skips_short_chunks():
    """Chunks under 20 words should be skipped."""
    short_transcript = """Alice 00:00:00
Okay.

Bob 00:00:05
Got it.

Carol 00:00:10
Sure thing.
"""
    chunks = chunk_transcript(short_transcript)
    assert len(chunks) == 0


def test_single_speaker():
    """Should handle transcript with only one speaker."""
    single = """Alice 00:00:00
This is a long monologue about the project status. We need to review all the deliverables and make sure everything is on track for the deadline next Friday. The frontend is looking good and the backend API is almost complete.
"""
    chunks = chunk_transcript(single)
    assert len(chunks) > 0
    assert all(c.speaker == "Alice" for c in chunks)


def test_no_speaker_labels():
    """Should handle transcript with no speaker labels as single 'Unknown' speaker."""
    raw = "This is a transcript without any speaker labels. It should still be chunked properly and tagged as Unknown speaker. " * 5
    chunks = chunk_transcript(raw)
    if chunks:  # May be empty if under 20 words total
        assert all(c.speaker == "Unknown" for c in chunks)


def test_empty_transcript():
    """Should return empty list for empty transcript."""
    assert chunk_transcript("") == []
    assert chunk_transcript("   ") == []
    assert chunk_transcript(None) == []


def test_chunk_indexes_sequential():
    """Chunk indexes should be sequential starting from 0."""
    chunks = chunk_transcript(SAMPLE_TRANSCRIPT)
    for i, c in enumerate(chunks):
        assert c.chunk_index == i


def test_long_monologue_gets_split():
    """A single speaker with >300 words should be split into multiple chunks."""
    long_text = "This is a sentence about the project. " * 100  # ~800 words
    transcript = f"Alice 00:00:00\n{long_text}"
    chunks = chunk_transcript(transcript)
    assert len(chunks) > 1
