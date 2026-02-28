from typing import Optional


def _to_float(x) -> Optional[float]:
    try:
        if x is None or x == "":
            return None
        return float(x)
    except Exception:
        return None


def pick_best(rows: list[dict]) -> Optional[dict]:
    if not rows:
        return None

    # ignore failed runs
    rows = [r for r in rows if (r.get("status") or "ok") != "failed"]
    if not rows:
        return None

    scored = []
    for r in rows:
        w = _to_float(r.get("wer"))
        c = _to_float(r.get("cer"))
        wall = _to_float(r.get("wall_time_sec")) or 10 ** 18
        rtf = _to_float(r.get("rtf")) or 10 ** 18
        scored.append((w, c, wall, rtf, r))

    has_wer = any(x[0] is not None for x in scored)

    if has_wer:
        def key(t):
            w, c, wall, rtf, _r = t
            return (
                w if w is not None else 10 ** 18,
                c if c is not None else 10 ** 18,
                wall,
                rtf,
            )
    else:
        def key(t):
            _w, _c, wall, rtf, _r = t
            return (wall, rtf)

    scored.sort(key=key)
    return scored[0][4]
