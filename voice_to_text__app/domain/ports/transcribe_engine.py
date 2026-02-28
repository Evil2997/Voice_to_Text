from pathlib import Path
from typing import Optional, Protocol

from voice_to_text__app.domain.models import TranscribeConfig


class TranscribeEngine(Protocol):
    """
    Порт для движка транскрибации.

    Domain знает только про контракт "получить текст из WAV",
    но не знает про faster-whisper, WhisperModel, GPU/CPU и т.д.
    """

    def transcribe(self, wav_path: Path, cfg: TranscribeConfig) -> tuple[str, Optional[str]]:
        ...
