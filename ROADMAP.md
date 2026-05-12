# Roadmap

## Current State

The project is a stable, production-ready CLI with clean architecture, deterministic caching, SQLite persistence, and a benchmark mode for finding optimal Whisper configurations. This is the foundation everything below builds on.

---

## Near Term

**Tests**
Unit tests for `run_logic.py` (cache hit/miss logic) and `selection.py` (pick_best ranking). These are pure functions with no I/O — straightforward to cover.

**Packaging**
- Proper `extras` in `pyproject.toml`: `faster-whisper` as optional, `jiwer` under `[bench]`
- CLI entry point: `v2t` command instead of `python main.py`
- `.python-version` file for reproducible environment

**Code quality**
- `ruff` for linting and formatting
- `pre-commit` hooks

---

## Medium Term

**LLM post-processing layer**
After transcription, pass the text through an LLM for:
- Summarization
- Structured extraction (topics, action items, key moments)
- Cleanup of filler words and repetitions

This requires a new `Transcript` domain entity and a `PostProcessor` port.

**Hotwords / prompt support**
For Russian speech with English technical terms, passing domain-specific vocabulary as Whisper `initial_prompt` or `hotwords` significantly improves accuracy without changing the model.

**Multilingual improvements**
Evaluate `language="ru"` vs `language="auto"` on mixed Russian/English content. Auto-detect works per-segment on large models but explicit `ru` often wins for code-switching with anglicisms.

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

**Infrastructure options**
- Redis for job queue and deduplication
- Postgres instead of SQLite for multi-worker setups
- Docker image with all dependencies (ffmpeg, yt-dlp, faster-whisper)
- GitHub Actions for CI

**CUDA support**
Current bench matrix is CPU-only (int8). Extend matrix to include CUDA + float16 combinations when GPU is available.

---

## Non-Goals

- Web UI (out of scope for this tool)
- Real-time / streaming transcription
- Audio recording (input only, no capture)
