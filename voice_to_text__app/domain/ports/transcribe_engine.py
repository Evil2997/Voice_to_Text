from pathlib import Path
from typing import Protocol

from voice_to_text__app.domain.models import Transcript, TranscribeConfig


class TranscribeEngine(Protocol):
    """
    Port for the transcription engine.

    Domain knows only the contract: receive structured Transcript from WAV.
    Infrastructure (faster-whisper, GPU/CPU) is hidden behind this port.
    """

    def transcribe(self, wav_path: Path, cfg: TranscribeConfig) -> Transcript:
        ...
