import sys
from typing import Any


def _coerce_value(raw: str) -> Any:
    # bool
    if raw.lower() in {"true", "1", "yes", "y", "on"}:
        return True
    if raw.lower() in {"false", "0", "no", "n", "off"}:
        return False

    # int
    if raw.isdigit() or (raw.startswith("-") and raw[1:].isdigit()):
        try:
            return int(raw)
        except Exception:
            pass

    # float
    try:
        if "." in raw or "e" in raw.lower():
            return float(raw)
    except Exception:
        pass

    # IMPORTANT:
    # Do NOT auto-coerce to Path.
    # Let Pydantic cast types based on Settings schema.
    return raw


def _set_nested(d: dict[str, Any], key: str, value: Any) -> None:
    parts = key.split(".")
    cur = d
    for p in parts[:-1]:
        cur = cur.setdefault(p, {})
    cur[parts[-1]] = value


def parse_argv(argv: list[str] | None = None) -> dict[str, Any]:
    if argv is None:
        argv = sys.argv[1:]

    out: dict[str, Any] = {}
    i = 0
    while i < len(argv):
        token = argv[i]
        if not token.startswith("--"):
            i += 1
            continue

        key = token[2:]

        # flag without value: --whisper.vad
        if i + 1 >= len(argv) or argv[i + 1].startswith("--"):
            _set_nested(out, key, True)
            i += 1
            continue

        raw_val = argv[i + 1]

        # comma-separated lists (bench matrix)
        if "," in raw_val:
            items = [x.strip() for x in raw_val.split(",") if x.strip()]
            coerced = tuple(_coerce_value(x) for x in items)
            _set_nested(out, key, coerced)
        else:
            _set_nested(out, key, _coerce_value(raw_val))

        i += 2

    return out
