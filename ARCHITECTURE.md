# Architecture

## Origin

The project started as a single-script transcription utility using faster-whisper. Over several iterations it evolved into a layered CLI system with clean separation of concerns, deterministic caching, and a benchmark mode for finding optimal Whisper configurations.

---

## Layer Structure

```
Domain ← Application ← Infrastructure ← CLI
```

Each layer depends only on the layer to its left. The CLI is the only place where concrete implementations are assembled.

### Domain
Owns the business rules and contracts. Has no knowledge of SQLite, Whisper, ffmpeg, or any external tool.

- `models.py` — core data structures: `PreparedTarget`, `TranscribeConfig`, `RunResult`, `RunMetrics`
- `run_logic.py` — single-run orchestration: cache check, transcription, metrics, persistence
- `exceptions.py` — domain-level exceptions
- `ports/` — Protocol interfaces that Infrastructure must implement

### Application
Orchestrates business scenarios using domain logic and ports. Does not implement low-level details.

- `prod_service.py` — single-file transcription flow
- `bench_service.py` — matrix iteration, progress tracking, scoring trigger, best-config selection
- `matrix.py` — generates `TranscribeConfig` combinations from bench settings
- `scoring.py` — WER/CER computation via jiwer against a reference transcript
- `selection.py` — `pick_best`: ranks by WER → CER → wall_time → RTF (falls back to wall_time → RTF if no scoring)

### Infrastructure
Concrete implementations of domain ports. No business logic here.

- `WhisperEngine` — manages faster-whisper model lifecycle; model loads once and is reused across bench iterations
- `SqliteRunRepository` — SQLite-backed implementation of `RunRepository`; uses `run_key` as primary key with upsert
- `AudioTargetPreparer` — downloads via yt-dlp, normalizes to 16 kHz mono PCM WAV via ffmpeg, caches result
- `Settings` — pydantic-settings with three sources: CLI argv → ENV → defaults

### CLI (Composition Root)
`entrypoint.py` is the only place where concrete implementations are instantiated and wired together. Nothing else knows about `SqliteRunRepository` or `WhisperEngine` by name.

---

## Key Design Decisions

### Ports belong to the consumer
`RunRepository`, `TranscribeEngine`, and `TargetPreparer` are defined in `domain/ports/`, not in infrastructure. Domain defines what it needs; infrastructure fulfills it.

### Deterministic run_key
Every transcription run is identified by a stable key composed of all parameters that affect the output:
```
target_id | model | device | compute_type | threads | workers | beam_size | patience | vad | lang
```
This makes caching exact and reproducible. The same audio with the same config always produces the same key.

### Strict two-condition cache
A run is considered cached only if **both** the `.txt` file exists on disk **and** the `run_key` is present in SQLite. Either alone is not enough. This prevents stale cache hits after manual cleanup.

### WhisperModel loaded once
In bench mode, the model would otherwise reload for every matrix combination. `WhisperEngine` tracks the current device and compute type and reloads only when they change — which in bench (CPU-only) means never.

### Custom CLI parser
Settings are resolved via a custom `parse_argv` that supports nested keys (`--whisper.threads 8`, `--bench.beams 1,5,10`) and type coercion without argparse. Priority: CLI → ENV → defaults.

### No global state
No module-level singletons. All dependencies are passed explicitly from the composition root.

---

## Data Flow

### PROD
```
target (file/URL)
  → AudioTargetPreparer.prepare()
      → yt-dlp (if URL)
      → ffmpeg normalize → 16kHz mono WAV (cached)
  → run_once()
      → compute run_key
      → check cache (txt + sqlite)
      → WhisperEngine.transcribe()
      → write .txt
      → SqliteRunRepository.upsert()
  → RunResult
```

### BENCH
```
target
  → prepare (same as prod)
  → ffmpeg make_sample (first N seconds, cached)
  → for each config in matrix:
      → run_once() with allow_skip=True
  → score_bench_repo() (WER/CER if ref provided)
  → pick_best()
```

---

## Workspace Layout

```
workspace/                           # configurable via --out-dir
├── prepared/
│   └── audio__<target_id>.wav      # normalized WAV cache
├── sample/
│   └── audio_sample_120.wav        # bench sample cache
├── <base_name>.txt                  # prod transcription result
├── <base_name>__<run_id>.txt        # bench results (one per config)
├── runs.sqlite                      # prod run history
└── bench.sqlite                     # bench run history + metrics
```

---

## Potential Next Steps

- **Resume support** — detect existing `.sqlite` on startup and skip already-completed runs without re-checking filesystem
- **LLM post-processing** — `Transcript` entity → summary / structured extraction layer
- **Telegram integration** — Telegram → RabbitMQ → Worker → Transcribe → Response (planned extension)
- **Batch mode** — queue of targets processed sequentially with shared engine lifecycle
- **Docker image** — portable environment with ffmpeg, yt-dlp, and faster-whisper pre-installed
