import logging
from pathlib import Path

from voice_to_text__app.domain.models import RunResult, TranscribeConfig
from voice_to_text__app.domain.ports.run_repository import RunRepository
from voice_to_text__app.domain.ports.target_preparer import TargetPreparer
from voice_to_text__app.domain.ports.transcribe_engine import TranscribeEngine
from voice_to_text__app.domain.run_logic import run_once

logger = logging.getLogger(__name__)


def transcribe(
        *,
        target: str,
        cfg: TranscribeConfig,
        out_dir: Path,
        repo: RunRepository,
        engine: TranscribeEngine,
        preparer: TargetPreparer,
) -> RunResult:
    out_dir = out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    prepared = preparer.prepare(target, work_dir=out_dir)

    res = run_once(
        prepared=prepared,
        cfg=cfg,
        out_dir=out_dir,
        repo=repo,
        engine=engine,
        bench_naming=False,
        allow_skip=True,
    )

    logger.info(
        "PROD done | cached=%s | txt=%s | wall=%.2fs | rtf=%s | lang=%s",
        "yes" if res.cached else "no",
        res.output_txt,
        res.metrics.wall_time_sec,
        f"{res.metrics.rtf:.3f}" if res.metrics.rtf is not None else "n/a",
        res.detected_language or "n/a",
    )
    return res
