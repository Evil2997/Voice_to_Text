from pathlib import Path

from jiwer import cer, wer

from voice_to_text__app.domain.ports.run_repository import RunRepository


def score_bench_repo(repo: RunRepository, ref_path: Path) -> int:
    """
    Добавляет/обновляет wer/cer для всех ok-run, у которых существует output_txt.
    Возвращает количество обновлённых строк.
    """
    ref_text = ref_path.read_text(encoding="utf-8")

    rows = repo.list_all()
    updated = 0

    for row in rows:
        if (row.get("status") or "ok") == "failed":
            continue

        out_txt = row.get("output_txt") or ""
        if not out_txt:
            continue

        p = Path(out_txt)
        if not p.exists():
            continue

        hyp = p.read_text(encoding="utf-8")
        w = wer(ref_text, hyp)
        c = cer(ref_text, hyp)

        row["wer"] = float(f"{w:.6f}")
        row["cer"] = float(f"{c:.6f}")
        repo.upsert(row)
        updated += 1

    return updated
