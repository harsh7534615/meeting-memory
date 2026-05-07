"""
Transcript chunker — splits Google Meet transcripts into overlapping chunks.

Algorithm:
1. Parse speaker turns — split on pattern: "Speaker Name HH:MM:SS"
2. Group consecutive turns by the same speaker
3. If a segment > 300 words, split at sentence boundary nearest to 200 words
4. Apply overlap: last 2 sentences of chunk[N] = first 2 of chunk[N+1]
5. Tag each chunk: { text, speaker, start_time, end_time, word_count }
6. Skip chunks < 20 words
"""
import re
from dataclasses import dataclass


@dataclass
class Chunk:
    text: str
    speaker: str
    start_time: str
    end_time: str
    word_count: int
    chunk_index: int


# Pattern: "Speaker Name HH:MM:SS" or "Speaker Name\tHH:MM:SS"
SPEAKER_TURN_PATTERN = re.compile(
    r"^(.+?)\s+(\d{1,2}:\d{2}(?::\d{2})?)\s*$", re.MULTILINE
)

MAX_CHUNK_WORDS = 300
TARGET_SPLIT_WORDS = 200
MIN_CHUNK_WORDS = 20


@dataclass
class _SpeakerSegment:
    speaker: str
    start_time: str
    end_time: str
    text: str


def _split_sentences(text: str) -> list[str]:
    """Split text into sentences. Handles common abbreviations."""
    # Split on period/question/exclamation followed by space and uppercase letter
    sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z])", text)
    # Fallback: if no splits, try splitting on just period+space
    if len(sentences) <= 1:
        sentences = re.split(r"(?<=[.!?])\s+", text)
    return [s.strip() for s in sentences if s.strip()]


def _get_last_n_sentences(text: str, n: int = 2) -> str:
    """Get the last N sentences from text."""
    sentences = _split_sentences(text)
    return " ".join(sentences[-n:]) if len(sentences) >= n else text


def _get_first_n_sentences(text: str, n: int = 2) -> str:
    """Get the first N sentences from text."""
    sentences = _split_sentences(text)
    return " ".join(sentences[:n]) if len(sentences) >= n else text


def _parse_speaker_turns(transcript: str) -> list[_SpeakerSegment]:
    """Parse raw transcript into speaker segments."""
    matches = list(SPEAKER_TURN_PATTERN.finditer(transcript))

    if not matches:
        # No speaker labels found — treat entire transcript as single speaker
        return [_SpeakerSegment(
            speaker="Unknown",
            start_time="00:00:00",
            end_time="00:00:00",
            text=transcript.strip(),
        )]

    segments = []
    for i, match in enumerate(matches):
        speaker = match.group(1).strip()
        start_time = match.group(2).strip()

        # Text runs from end of this match to start of next match (or end of string)
        text_start = match.end()
        text_end = matches[i + 1].start() if i + 1 < len(matches) else len(transcript)
        text = transcript[text_start:text_end].strip()

        if not text:
            continue

        # End time is the start of the next turn, or same as start
        end_time = matches[i + 1].group(2).strip() if i + 1 < len(matches) else start_time

        segments.append(_SpeakerSegment(
            speaker=speaker,
            start_time=start_time,
            end_time=end_time,
            text=text,
        ))

    return segments


def _merge_consecutive_speakers(segments: list[_SpeakerSegment]) -> list[_SpeakerSegment]:
    """Merge consecutive segments by the same speaker."""
    if not segments:
        return []

    merged = [segments[0]]
    for seg in segments[1:]:
        if seg.speaker == merged[-1].speaker:
            merged[-1].text += " " + seg.text
            merged[-1].end_time = seg.end_time
        else:
            merged.append(seg)

    return merged


def _split_long_segment(segment: _SpeakerSegment) -> list[_SpeakerSegment]:
    """Split a segment that exceeds MAX_CHUNK_WORDS at sentence boundaries."""
    words = segment.text.split()
    if len(words) <= MAX_CHUNK_WORDS:
        return [segment]

    sentences = _split_sentences(segment.text)
    parts = []
    current_sentences = []
    current_word_count = 0

    for sentence in sentences:
        sentence_words = len(sentence.split())
        if current_word_count + sentence_words > MAX_CHUNK_WORDS and current_sentences:
            parts.append(" ".join(current_sentences))
            current_sentences = []
            current_word_count = 0
        current_sentences.append(sentence)
        current_word_count += sentence_words

    if current_sentences:
        parts.append(" ".join(current_sentences))

    result = []
    for part in parts:
        result.append(_SpeakerSegment(
            speaker=segment.speaker,
            start_time=segment.start_time,
            end_time=segment.end_time,
            text=part,
        ))

    return result


def chunk_transcript(transcript: str) -> list[Chunk]:
    """
    Main entry point: parse transcript text into overlapping chunks.

    Returns a list of Chunk objects ready for embedding.
    """
    if not transcript or not transcript.strip():
        return []

    # Step 1: Parse speaker turns
    segments = _parse_speaker_turns(transcript)

    # Step 2: Merge consecutive same-speaker segments
    segments = _merge_consecutive_speakers(segments)

    # Step 3: Split long segments
    split_segments = []
    for seg in segments:
        split_segments.extend(_split_long_segment(seg))

    # Step 4: Build chunks with overlap
    chunks = []
    overlap_prefix = ""

    for i, seg in enumerate(split_segments):
        text = seg.text
        if overlap_prefix and i > 0:
            text = overlap_prefix + " " + text

        word_count = len(text.split())

        # Step 6: Skip chunks < 20 words
        if word_count < MIN_CHUNK_WORDS:
            continue

        chunks.append(Chunk(
            text=text,
            speaker=seg.speaker,
            start_time=seg.start_time,
            end_time=seg.end_time,
            word_count=word_count,
            chunk_index=len(chunks),
        ))

        # Prepare overlap for next chunk: last 2 sentences
        overlap_prefix = _get_last_n_sentences(seg.text, 2)

    return chunks
