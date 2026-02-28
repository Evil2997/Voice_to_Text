from pathlib import Path

from voice_to_text__app.domain.models import PreparedTarget
from voice_to_text__app.domain.ports.target_preparer import TargetPreparer
from voice_to_text__app.infrastructure.audio.targets import prepare_target, ffmpeg_make_sample


class AudioTargetPreparer(TargetPreparer):
    def prepare(self, target: str, *, work_dir: Path) -> PreparedTarget:
        return prepare_target(target, work_dir=work_dir)

    def make_sample(self, *, src_wav: Path, dst_wav: Path, seconds: int) -> Path:
        ffmpeg_make_sample(src_wav, dst_wav, seconds=seconds)
        return dst_wav
