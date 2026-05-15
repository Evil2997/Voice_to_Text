from pathlib import Path
from typing import Literal, Optional

from pydantic import BaseModel, Field


class PreparedTarget(BaseModel):
    target: str
    target_id: str
    base_name: str
    wav_path: Path
    audio_duration_sec: Optional[float] = None


class TranscribeConfig(BaseModel):
    model: str
    device: str
    compute_type: Optional[str] = None
    threads: int = Field(ge=1)
    workers: int = Field(ge=1)
    beam_size: int = Field(ge=1)
    patience: float = Field(ge=0.0)
    vad: bool = False
    lang: str = "auto"


# ---------------------------------------------------------------------------
# Structured transcript
# ---------------------------------------------------------------------------

class TranscriptSegment(BaseModel):
    start: float
    end: float
    text: str


class Transcript(BaseModel):
    segments: list[TranscriptSegment]
    language: Optional[str] = None
    duration_sec: Optional[float] = None

    def to_text(self) -> str:
        return " ".join(seg.text for seg in self.segments).strip()

    def to_srt(self) -> str:
        def _fmt(seconds: float) -> str:
            h = int(seconds // 3600)
            m = int((seconds % 3600) // 60)
            s = int(seconds % 60)
            ms = int(round((seconds % 1) * 1000))
            return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

        lines: list[str] = []
        for i, seg in enumerate(self.segments, 1):
            lines += [str(i), f"{_fmt(seg.start)} --> {_fmt(seg.end)}", seg.text.strip(), ""]
        return "\n".join(lines)

    def to_vtt(self) -> str:
        def _fmt(seconds: float) -> str:
            h = int(seconds // 3600)
            m = int((seconds % 3600) // 60)
            s = int(seconds % 60)
            ms = int(round((seconds % 1) * 1000))
            return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"

        lines: list[str] = ["WEBVTT", ""]
        for seg in self.segments:
            lines += [f"{_fmt(seg.start)} --> {_fmt(seg.end)}", seg.text.strip(), ""]
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Run result
# ---------------------------------------------------------------------------

class RunMetrics(BaseModel):
    wall_time_sec: float
    audio_duration_sec: Optional[float] = None
    rtf: Optional[float] = None


class RunResult(BaseModel):
    run_key: str
    target_id: str
    output_txt: Path
    output_json: Optional[Path] = None
    detected_language: Optional[str] = None
    metrics: RunMetrics
    cached: bool = False

    status: Literal["ok", "failed"] = "ok"
    error: Optional[str] = None
