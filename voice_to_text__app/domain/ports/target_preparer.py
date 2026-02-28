from pathlib import Path
from typing import Protocol

from voice_to_text__app.domain.models import PreparedTarget


class TargetPreparer(Protocol):
    """
    Порт подготовки target -> PreparedTarget.

    Domain/Application знают только контракт.
    Infrastructure реализует (yt-dlp / ffmpeg / ffprobe и т.д.).
    """

    def prepare(self, target: str, *, work_dir: Path) -> PreparedTarget:
        ...

    def make_sample(self, *, src_wav: Path, dst_wav: Path, seconds: int) -> Path:
        ...