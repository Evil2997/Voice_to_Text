import logging
from pathlib import Path

from voice_to_text__app.application.bench.bench_service import run_bench
from voice_to_text__app.application.prod.prod_service import transcribe as prod_transcribe
from voice_to_text__app.domain.models import TranscribeConfig
from voice_to_text__app.infrastructure.audio.target_preparer import AudioTargetPreparer
from voice_to_text__app.infrastructure.cli.logging import configure_logging
from voice_to_text__app.infrastructure.config.settings import Settings
from voice_to_text__app.infrastructure.sqlite.sqlite_repo import SqliteRunRepository
from voice_to_text__app.infrastructure.whisper.whisper_engine import WhisperEngine

logger = logging.getLogger(__name__)


def run() -> int:
    settings = Settings()
    configure_logging(settings.log_level)

    out_dir: Path = settings.out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    logger.info(
        "Start | mode=%s | target=%s | out_dir=%s",
        settings.mode,
        settings.target,
        out_dir,
    )

    cfg = TranscribeConfig(**settings.whisper.model_dump())

    # composition root: собираем конкретные адаптеры здесь
    preparer = AudioTargetPreparer()
    engine = WhisperEngine(cfg.model)

    if settings.mode == "prod":
        repo = SqliteRunRepository(out_dir / "runs.sqlite")
        prod_transcribe(
            target=settings.target,
            cfg=cfg,
            out_dir=out_dir,
            repo=repo,
            engine=engine,
            preparer=preparer,
        )
        return 0

    if settings.mode == "bench":
        repo = SqliteRunRepository(out_dir / "bench.sqlite")
        run_bench(
            settings=settings,
            base_cfg=cfg,
            repo=repo,
            engine=engine,
            preparer=preparer,
        )
        return 0

    logger.error("Unknown mode=%r", settings.mode)
    return 2
