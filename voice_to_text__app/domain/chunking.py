"""
Algorithmic transcript chunking — no AI required.

Three strategies, all based on segment boundaries already provided by Whisper:

- chunk_by_pause   — new chunk on silence gap between segments
- chunk_by_time    — fixed time windows
- chunk_by_words   — fixed word count windows
"""

from voice_to_text__app.domain.models import Transcript, TranscriptSegment
from pydantic import BaseModel


class TranscriptChunk(BaseModel):
    start: float
    end: float
    text: str
    segment_count: int

    def word_count(self) -> int:
        return len(self.text.split())


def _segments_to_chunk(segments: list[TranscriptSegment]) -> TranscriptChunk:
    return TranscriptChunk(
        start=segments[0].start,
        end=segments[-1].end,
        text=" ".join(seg.text.strip() for seg in segments).strip(),
        segment_count=len(segments),
    )


def chunk_by_pause(
    transcript: Transcript,
    *,
    min_pause_sec: float = 1.5,
) -> list[TranscriptChunk]:
    """
    Split transcript into chunks on silence gaps between segments.

    A new chunk starts when the gap between end of the previous segment
    and start of the next exceeds min_pause_sec.

    Good for: interviews, lectures, conversations with natural pauses.
    """
    if not transcript.segments:
        return []

    chunks: list[TranscriptChunk] = []
    current: list[TranscriptSegment] = [transcript.segments[0]]

    for seg in transcript.segments[1:]:
        gap = seg.start - current[-1].end
        if gap >= min_pause_sec:
            chunks.append(_segments_to_chunk(current))
            current = [seg]
        else:
            current.append(seg)

    if current:
        chunks.append(_segments_to_chunk(current))

    return chunks


def chunk_by_time(
    transcript: Transcript,
    *,
    window_sec: float = 30.0,
) -> list[TranscriptChunk]:
    """
    Split transcript into fixed time windows.

    Each chunk covers at most window_sec seconds, measured from
    the start of the first segment in that chunk.

    Good for: uniform chunks for LLM context windows, predictable output size.
    """
    if not transcript.segments:
        return []

    chunks: list[TranscriptChunk] = []
    current: list[TranscriptSegment] = []
    window_start: float = transcript.segments[0].start

    for seg in transcript.segments:
        if current and (seg.start - window_start) >= window_sec:
            chunks.append(_segments_to_chunk(current))
            current = [seg]
            window_start = seg.start
        else:
            current.append(seg)

    if current:
        chunks.append(_segments_to_chunk(current))

    return chunks


def chunk_by_words(
    transcript: Transcript,
    *,
    max_words: int = 100,
) -> list[TranscriptChunk]:
    """
    Split transcript into chunks by word count.

    Accumulates segments until adding the next segment would exceed
    max_words. A single segment that alone exceeds max_words is kept
    as its own chunk — never split mid-segment.

    Good for: controlling token count before sending to LLM.
    """
    if not transcript.segments:
        return []

    chunks: list[TranscriptChunk] = []
    current: list[TranscriptSegment] = []
    current_words: int = 0

    for seg in transcript.segments:
        seg_words = len(seg.text.split())

        if current and (current_words + seg_words) > max_words:
            chunks.append(_segments_to_chunk(current))
            current = [seg]
            current_words = seg_words
        else:
            current.append(seg)
            current_words += seg_words

    if current:
        chunks.append(_segments_to_chunk(current))

    return chunks