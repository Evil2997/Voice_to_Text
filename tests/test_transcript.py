import pytest

from voice_to_text__app.domain.models import Transcript, TranscriptSegment


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_transcript(*segments: tuple, language: str = "en", duration: float = None) -> Transcript:
    """segments: list of (start, end, text) tuples"""
    return Transcript(
        segments=[TranscriptSegment(start=s, end=e, text=t) for s, e, t in segments],
        language=language,
        duration_sec=duration,
    )


SIMPLE = make_transcript(
    (0.0, 3.2, "Hello world."),
    (3.5, 7.1, "How are you?"),
)

SINGLE = make_transcript((0.0, 5.0, "One segment."))
EMPTY = Transcript(segments=[], language=None, duration_sec=None)


# ---------------------------------------------------------------------------
# to_text
# ---------------------------------------------------------------------------

class TestToText:
    def test_joins_segments_with_space(self):
        assert SIMPLE.to_text() == "Hello world. How are you?"

    def test_single_segment(self):
        assert SINGLE.to_text() == "One segment."

    def test_empty_transcript_returns_empty_string(self):
        assert EMPTY.to_text() == ""

    def test_strips_leading_trailing_whitespace(self):
        t = make_transcript((0.0, 1.0, "  hello  "), (1.0, 2.0, "  world  "))
        assert t.to_text() == "hello     world"

    def test_preserves_segment_text_content(self):
        t = make_transcript((0.0, 1.0, "Привет мир."))
        assert "Привет мир." in t.to_text()


# ---------------------------------------------------------------------------
# to_srt
# ---------------------------------------------------------------------------

class TestToSrt:
    def test_starts_with_index_1(self):
        lines = SIMPLE.to_srt().splitlines()
        assert lines[0] == "1"

    def test_second_block_has_index_2(self):
        lines = SIMPLE.to_srt().splitlines()
        # block 1: index, timecode, text, empty → 4 lines
        assert lines[4] == "2"

    def test_timecode_format(self):
        srt = SINGLE.to_srt()
        assert "00:00:00,000 --> 00:00:05,000" in srt

    def test_timecode_separator_is_comma(self):
        """SRT uses comma for milliseconds, not dot."""
        srt = SIMPLE.to_srt()
        assert "," in srt
        assert "." not in srt.split("-->")[0]

    def test_text_present_in_output(self):
        srt = SIMPLE.to_srt()
        assert "Hello world." in srt
        assert "How are you?" in srt

    def test_empty_transcript_produces_only_empty_string(self):
        assert EMPTY.to_srt().strip() == ""

    def test_hours_minutes_seconds_milliseconds_formatting(self):
        t = make_transcript((3661.5, 3665.0, "Late segment."))
        srt = t.to_srt()
        assert "01:01:01,500" in srt

    def test_blocks_separated_by_empty_line(self):
        srt = SIMPLE.to_srt()
        blocks = [b for b in srt.split("\n\n") if b.strip()]
        assert len(blocks) == 2


# ---------------------------------------------------------------------------
# to_vtt
# ---------------------------------------------------------------------------

class TestToVtt:
    def test_starts_with_webvtt_header(self):
        assert SIMPLE.to_vtt().startswith("WEBVTT")

    def test_timecode_separator_is_dot(self):
        """VTT uses dot for milliseconds, not comma."""
        vtt = SIMPLE.to_vtt()
        # skip header line, check first timecode line
        timecode_line = [l for l in vtt.splitlines() if "-->" in l][0]
        assert "." in timecode_line
        assert "," not in timecode_line

    def test_timecode_format(self):
        vtt = SINGLE.to_vtt()
        assert "00:00:00.000 --> 00:00:05.000" in vtt

    def test_text_present_in_output(self):
        vtt = SIMPLE.to_vtt()
        assert "Hello world." in vtt
        assert "How are you?" in vtt

    def test_empty_transcript_contains_only_header(self):
        vtt = EMPTY.to_vtt()
        lines = [l for l in vtt.splitlines() if l.strip()]
        assert lines == ["WEBVTT"]

    def test_no_numeric_block_indices(self):
        """VTT does not require numeric block indices like SRT."""
        vtt = SIMPLE.to_vtt()
        lines = vtt.splitlines()
        # after WEBVTT header, no line should be a bare integer
        for line in lines[1:]:
            assert not line.strip().isdigit()

    def test_hours_minutes_seconds_milliseconds_formatting(self):
        t = make_transcript((3661.5, 3665.0, "Late segment."))
        vtt = t.to_vtt()
        assert "01:01:01.500" in vtt


# ---------------------------------------------------------------------------
# SRT vs VTT difference
# ---------------------------------------------------------------------------

class TestSrtVsVtt:
    def test_srt_and_vtt_contain_same_text(self):
        srt = SIMPLE.to_srt()
        vtt = SIMPLE.to_vtt()
        assert "Hello world." in srt
        assert "Hello world." in vtt

    def test_millisecond_separator_differs(self):
        srt_time = [l for l in SIMPLE.to_srt().splitlines() if "-->" in l][0]
        vtt_time = [l for l in SIMPLE.to_vtt().splitlines() if "-->" in l][0]
        assert "," in srt_time
        assert "." in vtt_time