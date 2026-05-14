# Roadmap

## Done

**Clean Architecture**
Domain ← Application ← Infrastructure with inverted dependencies through ports. No global state, composition root in `entrypoint.py`.

**Deterministic caching**
`run_key` covers all parameters that affect output. Cache is strict: txt on disk **and** run_key in SQLite — either alone is not enough.

**Bench mode**
Full parameter matrix (threads × workers × beam × vad), WER/CER scoring via jiwer, automatic best-config selection in `pick_best`.

**Custom CLI parser**
Nested keys (`--whisper.threads 8`, `--bench.beams 1,5,10`), type coercion, comma-separated tuples — no argparse dependency.

**Unit tests**
`selection.py` (`_to_float`, `pick_best`), `run_logic.py` (`make_run_key`, `resolve_compute_type`, txt naming), `targets.py` (`is_url`, `_hash`), `cli_source.py` (`_coerce_value`, `parse_argv`). Pure functions only, no mocking of infrastructure.

---

## Near Term

**CI (GitHub Actions)**
Run `uv run pytest` on push/PR. Approximately 10 lines of YAML. Moves the project from "has tests" to "tests are enforced". This is the minimum bar for any serious repo.

**Packaging**
- `[project.scripts]`: `v2t = "voice_to_text__app.main:main"` — so the tool runs as `v2t` instead of `python main.py`
- `[dependency-groups]`: `dev = ["pytest>=8.0", "ruff>=0.4"]`
- `extras`: `faster-whisper` as optional install, `jiwer` under `[bench]`

**Code quality**
- `ruff` for linting and formatting (replaces flake8 + black + isort in one tool)
- `pre-commit` hooks: ruff + trailing whitespace + end-of-file

**.python-version file**
Pin `3.12` for reproducible `uv` environments.

---

## Medium Term

**LLM post-processing layer**
After transcription, pass the text through an LLM for summarization, structured extraction (topics, action items, key moments), and cleanup of filler words. Requires a new `Transcript` domain entity and a `PostProcessor` port — the architecture already supports this pattern.

**Hotwords / prompt support**
For Russian speech with English technical terms, passing domain vocabulary as Whisper `initial_prompt` or `hotwords` improves accuracy without changing the model. Measurable via bench WER before/after.

**Multilingual evaluation**
Benchmark `language="ru"` vs `language="auto"` on mixed Russian/English content. Auto-detect works per-segment on large models but explicit `ru` often wins for code-switching with anglicisms.

**Integration into PDFnik**
This tool is already used as a transcription microservice inside the PDFnik pipeline (`txt.transcribe`). Medium-term goal: formalize the interface so VTT can be updated independently without breaking PDFnik's contract.

---

## Long Term

**Telegram integration**
```
Telegram message (audio/video)
  → RabbitMQ queue
  → Worker (this tool)
  → Transcription
  → LLM post-processing
  → Response back to Telegram
```

**Infrastructure scaling**
- Redis for job queue and deduplication
- Postgres instead of SQLite for multi-worker setups
- Docker image with all dependencies (ffmpeg, yt-dlp, faster-whisper)

**CUDA support**
Current bench matrix is CPU-only (int8). Extend to include CUDA + float16 combinations when GPU is available. The matrix generator (`matrix.py`) already supports multiple compute types — only the defaults need extending.

---

## Non-Goals

- Web UI
- Real-time / streaming transcription
- Audio recording (input only, no capture)