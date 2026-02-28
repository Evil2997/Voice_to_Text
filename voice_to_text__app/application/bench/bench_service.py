import logging

from voice_to_text__app.application.bench.matrix import iter_matrix
from voice_to_text__app.application.bench.scoring import score_bench_repo
from voice_to_text__app.application.bench.selection import pick_best
from voice_to_text__app.domain.models import PreparedTarget, TranscribeConfig
from voice_to_text__app.domain.ports.run_repository import RunRepository
from voice_to_text__app.domain.ports.target_preparer import TargetPreparer
from voice_to_text__app.domain.ports.transcribe_engine import TranscribeEngine
from voice_to_text__app.domain.run_logic import run_once
from voice_to_text__app.infrastructure.config.settings import Settings

logger = logging.getLogger(__name__)


def run_bench(
        *,
        settings: Settings,
        base_cfg: TranscribeConfig,
        repo: RunRepository,
        engine: TranscribeEngine,
        preparer: TargetPreparer,
) -> None:
    out_dir = settings.out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    prepared = preparer.prepare(settings.target, work_dir=out_dir)

    sample_wav = out_dir / "sample" / f"{prepared.base_name}_sample_{settings.bench.sample_seconds}.wav"
    sample_wav.parent.mkdir(parents=True, exist_ok=True)

    if not sample_wav.exists():
        logger.info("Create sample: %s sec", settings.bench.sample_seconds)
        preparer.make_sample(src_wav=prepared.wav_path, dst_wav=sample_wav, seconds=settings.bench.sample_seconds)
    else:
        logger.info("Sample cached: %s", sample_wav.name)

    bench_prepared = PreparedTarget(
        target=prepared.target,
        target_id=f"{prepared.target_id}__sample_{settings.bench.sample_seconds}",
        base_name=f"{prepared.base_name}_sample_{settings.bench.sample_seconds}",
        wav_path=sample_wav,
        audio_duration_sec=float(settings.bench.sample_seconds),
    )

    total = 0
    executed = 0
    skipped = 0
    failed = 0

    try:
        for cfg in iter_matrix(base_cfg, settings=settings):
            total += 1
            res = run_once(
                prepared=bench_prepared,
                cfg=cfg,
                out_dir=out_dir,
                repo=repo,
                engine=engine,
                bench_naming=True,
                allow_skip=True,
            )

            if res.cached:
                skipped += 1
            elif res.status == "failed":
                failed += 1
            else:
                executed += 1

            if res.status == "failed":
                logger.warning(
                    "BENCH %d | failed | cached=%s | wall=%.2fs | txt=%s | error=%s",
                    total,
                    "yes" if res.cached else "no",
                    res.metrics.wall_time_sec,
                    res.output_txt.name,
                    res.error or "",
                )
            else:
                logger.info(
                    "BENCH %d | cached=%s | wall=%.2fs | rtf=%s | txt=%s",
                    total,
                    "yes" if res.cached else "no",
                    res.metrics.wall_time_sec,
                    f"{res.metrics.rtf:.3f}" if res.metrics.rtf is not None else "n/a",
                    res.output_txt.name,
                )

    except KeyboardInterrupt:
        logger.warning(
            "BENCH interrupted by user (Ctrl+C) | total=%d | executed=%d | skipped=%d | failed=%d",
            total,
            executed,
            skipped,
            failed,
        )
        return

    logger.info(
        "BENCH done | total=%d | executed=%d | skipped=%d | failed=%d",
        total,
        executed,
        skipped,
        failed,
    )

    if settings.bench.ref and settings.bench.ref.exists():
        updated = score_bench_repo(repo, settings.bench.ref)
        logger.info("SCORE done | updated=%d", updated)
    else:
        logger.warning("SCORE skipped | ref missing")

    best = pick_best(repo.list_all())
    if best:
        logger.info(
            "BEST | wer=%s | cer=%s | wall=%s | rtf=%s | txt=%s | cfg: thr=%s wrk=%s beam=%s pat=%s vad=%s compute=%s",
            best.get("wer", ""),
            best.get("cer", ""),
            best.get("wall_time_sec", ""),
            best.get("rtf", ""),
            best.get("output_txt", ""),
            best.get("threads", ""),
            best.get("workers", ""),
            best.get("beam_size", ""),
            best.get("patience", ""),
            best.get("vad", ""),
            best.get("compute_type", ""),
        )
    else:
        logger.warning("BEST not found (empty DB?)")
