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
`selection.py`, `run_logic.py`, `targets.py`, `cli_source.py`, `Transcript` methods, all three chunking strategies. Pure functions only, no infrastructure mocking.

**Structured transcript output**
`TranscriptSegment` and `Transcript` domain entities. Whisper segments (start, end, text) are preserved instead of discarded. Each run produces four artifacts: `.txt`, `.json`, `.srt`, `.vtt`. `TranscribeEngine` port returns `Transcript` — change isolated behind the port.

**CI (GitHub Actions)**
`uv run pytest` runs on every push and pull request to `main`.

**pre-commit**
ruff + ruff-format + mypy hooks. Install: `uv run pre-commit install`.

**Algorithmic chunking**
Three strategies in `domain/chunking.py`, no AI required:
- `chunk_by_pause` — splits on silence gaps between segments
- `chunk_by_time` — fixed time windows
- `chunk_by_words` — fixed word count windows (useful for controlling LLM token usage)

Each chunk is a `TranscriptChunk` with `start`, `end`, `text`, `segment_count`.

---

## Near Term

**LLM post-processing**
With chunking in place, sending structured segments to an LLM is the natural next step. Each chunk is a self-contained unit with known boundaries — much better input than a flat string.

Planned capabilities:
- Summary per chunk and full transcript
- Action item extraction
- Key moment detection
- Chapter / topic labeling

Requires a `PostProcessor` port and a new application-layer service. Domain stays unchanged.

---

## Medium Term

**Search / RAG**
Structured transcripts map naturally to vector indexes. Timestamp-aware retrieval enables queries like "at what moment did they discuss X?" over audio and video content.

**Integration into PDFnik**
VTT is already used as a transcription microservice inside PDFnik (`txt.transcribe`). `Transcript` becomes the shared contract between services, replacing the current plain-text hand-off.

---

## Long Term

**Telegram integration**
```
Telegram message (audio/video)
  → RabbitMQ queue
  → Worker (this tool)
  → Transcript (structured)
  → LLM post-processing
  → Response back to Telegram
```

**Infrastructure scaling**
- Redis for job queue and deduplication
- Postgres instead of SQLite for multi-worker setups
- Docker image with all dependencies (ffmpeg, yt-dlp, faster-whisper)

**CUDA support**
Extend bench matrix to include CUDA + float16 combinations. `matrix.py` already supports multiple compute types — only the defaults need extending.

---

## Non-Goals

- Web UI
- Real-time / streaming transcription
- Audio recording (input only, no capture)