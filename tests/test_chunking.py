import pytest

from voice_to_text__app.domain.models import Transcript, TranscriptSegment
from voice_to_text__app.domain.chunking import (
    TranscriptChunk,
    chunk_by_pause,
    chunk_by_time,
    chunk_by_words,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def seg(start: float, end: float, text: str) -> TranscriptSegment:
    return TranscriptSegment(start=start, end=end, text=text)


def transcript(*segments: TranscriptSegment) -> Transcript:
    return Transcript(segments=list(segments))


# ---------------------------------------------------------------------------
# chunk_by_pause
# ---------------------------------------------------------------------------

class TestChunkByPause:
    def test_empty_transcript_returns_empty(self):
        assert chunk_by_pause(Transcript(segments=[])) == []

    def test_single_segment_returns_one_chunk(self):
        t = transcript(seg(0.0, 3.0, "Hello."))
        chunks = chunk_by_pause(t, min_pause_sec=1.5)
        assert len(chunks) == 1
        assert chunks[0].text == "Hello."

    def test_splits_on_gap_above_threshold(self):
        t = transcript(
            seg(0.0, 3.0, "First part."),
            seg(6.0, 9.0, "Second part."),  # gap = 3.0s
        )
        chunks = chunk_by_pause(t, min_pause_sec=1.5)
        assert len(chunks) == 2

    def test_no_split_on_gap_below_threshold(self):
        t = transcript(
            seg(0.0, 3.0, "First."),
            seg(3.5, 6.0, "Second."),  # gap = 0.5s
        )
        chunks = chunk_by_pause(t, min_pause_sec=1.5)
        assert len(chunks) == 1

    def test_gap_exactly_at_threshold_splits(self):
        t = transcript(
            seg(0.0, 3.0, "A."),
            seg(4.5, 6.0, "B."),  # gap = exactly 1.5s
        )
        chunks = chunk_by_pause(t, min_pause_sec=1.5)
        assert len(chunks) == 2

    def test_chunk_text_joins_segments(self):
        t = transcript(
            seg(0.0, 1.0, "Hello"),
            seg(1.1, 2.0, "world."),
        )
        chunks = chunk_by_pause(t, min_pause_sec=5.0)
        assert chunks[0].text == "Hello world."

    def test_chunk_start_end_correct(self):
        t = transcript(
            seg(1.0, 3.0, "A."),
            seg(3.2, 5.0, "B."),
        )
        chunks = chunk_by_pause(t, min_pause_sec=5.0)
        assert chunks[0].start == 1.0
        assert chunks[0].end == 5.0

    def test_segment_count_correct(self):
        t = transcript(
            seg(0.0, 1.0, "A."),
            seg(1.1, 2.0, "B."),
            seg(2.1, 3.0, "C."),
        )
        chunks = chunk_by_pause(t, min_pause_sec=5.0)
        assert chunks[0].segment_count == 3

    def test_multiple_splits(self):
        t = transcript(
            seg(0.0, 1.0, "A."),
            seg(5.0, 6.0, "B."),   # gap 4s
            seg(11.0, 12.0, "C."), # gap 5s
        )
        chunks = chunk_by_pause(t, min_pause_sec=2.0)
        assert len(chunks) == 3


# ---------------------------------------------------------------------------
# chunk_by_time
# ---------------------------------------------------------------------------

class TestChunkByTime:
    def test_empty_transcript_returns_empty(self):
        assert chunk_by_time(Transcript(segments=[])) == []

    def test_single_segment_returns_one_chunk(self):
        t = transcript(seg(0.0, 5.0, "Hello."))
        assert len(chunk_by_time(t, window_sec=30.0)) == 1

    def test_splits_when_window_exceeded(self):
        t = transcript(
            seg(0.0, 10.0, "A."),
            seg(10.0, 20.0, "B."),
            seg(31.0, 40.0, "C."),  # starts 31s after first → new window
        )
        chunks = chunk_by_time(t, window_sec=30.0)
        assert len(chunks) == 2

    def test_no_split_within_window(self):
        t = transcript(
            seg(0.0, 10.0, "A."),
            seg(15.0, 25.0, "B."),
            seg(25.0, 29.0, "C."),
        )
        chunks = chunk_by_time(t, window_sec=30.0)
        assert len(chunks) == 1

    def test_chunk_boundaries_are_segment_boundaries(self):
        t = transcript(
            seg(0.0, 5.0, "A."),
            seg(35.0, 40.0, "B."),
        )
        chunks = chunk_by_time(t, window_sec=30.0)
        assert chunks[0].start == 0.0
        assert chunks[0].end == 5.0
        assert chunks[1].start == 35.0
        assert chunks[1].end == 40.0

    def test_window_measured_from_chunk_start(self):
        """Window resets at each chunk start, not from transcript start."""
        t = transcript(
            seg(0.0, 1.0, "A."),
            seg(31.0, 32.0, "B."),  # new chunk, window resets to 31.0
            seg(55.0, 56.0, "C."),  # 55 - 31 = 24s < 30s, stays in chunk 2
            seg(62.0, 63.0, "D."),  # 62 - 31 = 31s >= 30s, new chunk
        )
        chunks = chunk_by_time(t, window_sec=30.0)
        assert len(chunks) == 3


# ---------------------------------------------------------------------------
# chunk_by_words
# ---------------------------------------------------------------------------

class TestChunkByWords:
    def test_empty_transcript_returns_empty(self):
        assert chunk_by_words(Transcript(segments=[])) == []

    def test_single_segment_returns_one_chunk(self):
        t = transcript(seg(0.0, 5.0, "one two three"))
        assert len(chunk_by_words(t, max_words=100)) == 1

    def test_splits_when_word_count_exceeded(self):
        t = transcript(
            seg(0.0, 1.0, "one two three"),    # 3 words
            seg(1.0, 2.0, "four five six"),     # 3 words → total 6
            seg(2.0, 3.0, "seven eight nine"),  # 3 words → total 9 > 7
        )
        chunks = chunk_by_words(t, max_words=7)
        assert len(chunks) == 2

    def test_no_split_within_limit(self):
        t = transcript(
            seg(0.0, 1.0, "one two"),
            seg(1.0, 2.0, "three four"),
            seg(2.0, 3.0, "five six"),
        )
        chunks = chunk_by_words(t, max_words=10)
        assert len(chunks) == 1

    def test_oversized_single_segment_becomes_own_chunk(self):
        """A segment exceeding max_words is never split — kept whole."""
        t = transcript(
            seg(0.0, 5.0, "a b c d e f g h i j"),  # 10 words
        )
        chunks = chunk_by_words(t, max_words=5)
        assert len(chunks) == 1
        assert chunks[0].word_count() == 10

    def test_word_count_method(self):
        chunk = TranscriptChunk(start=0.0, end=1.0, text="one two three", segment_count=1)
        assert chunk.word_count() == 3

    def test_chunk_text_correct(self):
        t = transcript(
            seg(0.0, 1.0, "hello world"),
            seg(5.0, 6.0, "next chunk here"),
        )
        chunks = chunk_by_words(t, max_words=2)
        assert chunks[0].text == "hello world"
        assert chunks[1].text == "next chunk here"

    def test_segment_count_tracked(self):
        t = transcript(
            seg(0.0, 1.0, "a b"),
            seg(1.0, 2.0, "c d"),
            seg(2.0, 3.0, "e f g h i j"),  # exceeds → new chunk
        )
        chunks = chunk_by_words(t, max_words=5)
        assert chunks[0].segment_count == 2
        assert chunks[1].segment_count == 1


# ---------------------------------------------------------------------------
# General contract across all strategies
# ---------------------------------------------------------------------------

class TestChunkingContract:
    STRATEGIES = [
        lambda t: chunk_by_pause(t, min_pause_sec=1.5),
        lambda t: chunk_by_time(t, window_sec=30.0),
        lambda t: chunk_by_words(t, max_words=100),
    ]

    def _full_transcript(self):
        return transcript(
            seg(0.0, 3.0, "Hello world."),
            seg(3.5, 6.0, "How are you?"),
            seg(6.5, 9.0, "I am fine."),
        )

    def test_all_text_preserved(self):
        """No segment text is lost across any strategy."""
        t = self._full_transcript()
        original_text = " ".join(s.text.strip() for s in t.segments)
        for strategy in self.STRATEGIES:
            chunks = strategy(t)
            combined = " ".join(c.text for c in chunks)
            for word in original_text.split():
                assert word in combined

    def test_chunks_are_time_ordered(self):
        """Chunks are always in chronological order."""
        t = self._full_transcript()
        for strategy in self.STRATEGIES:
            chunks = strategy(t)
            for i in range(len(chunks) - 1):
                assert chunks[i].end <= chunks[i + 1].start

    def test_no_empty_chunks(self):
        """No strategy produces chunks with empty text."""
        t = self._full_transcript()
        for strategy in self.STRATEGIES:
            for chunk in strategy(t):
                assert chunk.text.strip() != ""