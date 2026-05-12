# Voice → Text CLI

CLI tool for transcribing audio and video to text using [faster-whisper](https://github.com/SYSTRAN/faster-whisper).

Supports local files and YouTube URLs. Two modes: fast single-file transcription (`prod`) and full parameter matrix search for finding the optimal configuration (`bench`).

---

## What it does

- Local files and YouTube URLs (via `yt-dlp`)
- Automatic audio normalization → 16 kHz mono PCM WAV via `ffmpeg`
- Deterministic cache based on `run_key` — same file with same parameters never runs twice
- SQLite for storing all runs with metrics (wall time, RTF, WER, CER)
- `bench` mode: parameter matrix (threads × workers × beam × vad), WER/CER scoring via jiwer, automatic best-config selection
- Clean Architecture: Domain ← Application ← Infrastructure, dependencies inverted through ports
- Custom CLI parser with nested keys (`--whisper.threads 8`) — no argparse

---

## Stack

- **Python 3.12+**
- [faster-whisper](https://github.com/SYSTRAN/faster-whisper) — transcription engine
- [jiwer](https://github.com/jitsi/jiwer) — WER/CER scoring (bench with ref only)
- [Pydantic](https://docs.pydantic.dev/) + [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) — models and config
- [uv](https://github.com/astral-sh/uv) — dependency management
- System tools: `ffmpeg`, `ffprobe`, `yt-dlp`

---

## Requirements

```bash
# ffmpeg
sudo apt install ffmpeg

# yt-dlp (YouTube only)
pip install yt-dlp
```

---

## Installation

```bash
git clone https://github.com/Evil2997/voice-to-text-cli.git
cd voice-to-text-cli
uv sync
```

---

## Usage

### PROD — transcribe a file or URL

```bash
# Local file
uv run python main.py --mode prod --target ./audio.mp3

# YouTube
uv run python main.py --mode prod --target "https://youtu.be/..."

# Override model and device
uv run python main.py --mode prod --target ./audio.mp3 \
  --whisper.model large-v3 \
  --whisper.device cpu \
  --whisper.threads 8
```

### BENCH — find the best configuration

```bash
# Default matrix
uv run python main.py --mode bench --target ./audio.mp3 --bench.ref ./ref.txt

# Custom matrix
uv run python main.py --mode bench \
  --target ./audio.mp3 \
  --bench.threads 4,8,12 \
  --bench.beams 1,5,10 \
  --bench.sample-seconds 60 \
  --bench.ref ./ref.txt
```

`ref.txt` is the reference transcript for WER/CER scoring. Without it bench still runs but selects the best config by speed only.

---

## Configuration

Priority: CLI arguments → environment variables → defaults.

```bash
export VOICE2TEXT__MODE=prod
export VOICE2TEXT__TARGET=/path/to/audio.wav
export VOICE2TEXT__WHISPER__MODEL=large-v3
export VOICE2TEXT__WHISPER__THREADS=8
export VOICE2TEXT__OUT_DIR=./workspace
```

Full parameter list in `voice_to_text__app/infrastructure/config/settings.py`.

---

## Workspace layout

Default `./workspace` (configurable via `--out-dir`):

```
workspace/
├── prepared/                        # normalized WAV cache
├── sample/                          # bench samples
├── full_120__abc123.txt             # prod transcription result
├── full_120_sample_120__def456.txt  # bench results (one per config)
├── runs.sqlite                      # prod run history
└── bench.sqlite                     # bench run history + metrics
```

---

## Caching

The `run_key` includes: `target_id | model | device | compute_type | threads | workers | beam_size | patience | vad | lang`

A run is considered cached only if **both** the `.txt` file exists on disk **and** the `run_key` is present in SQLite.

---

## Project structure

```
voice_to_text__app/
├── domain/
│   ├── models.py                    # PreparedTarget, TranscribeConfig, RunResult
│   ├── exceptions.py
│   ├── run_logic.py                 # single-run logic: cache, transcribe, persist
│   └── ports/
│       ├── run_repository.py        # Protocol: get / upsert / list_all
│       ├── transcribe_engine.py     # Protocol: transcribe(wav, cfg)
│       └── target_preparer.py       # Protocol: prepare / make_sample
├── application/
│   ├── prod/
│   │   └── prod_service.py
│   └── bench/
│       ├── bench_service.py
│       ├── matrix.py                # config matrix generator
│       ├── scoring.py               # WER/CER via jiwer
│       └── selection.py             # pick_best
├── infrastructure/
│   ├── audio/
│   │   ├── targets.py               # yt-dlp, WAV normalization
│   │   ├── media.py                 # ffprobe: duration
│   │   ├── process.py               # run_cmd wrapper
│   │   └── target_preparer.py       # AudioTargetPreparer
│   ├── cli/
│   │   ├── entrypoint.py            # composition root
│   │   ├── cli_source.py            # argv parser without argparse
│   │   └── logging.py
│   ├── config/
│   │   └── settings.py
│   ├── sqlite/
│   │   ├── schema.py
│   │   └── sqlite_repo.py
│   └── whisper/
│       └── whisper_engine.py        # WhisperModel lifecycle
└── main.py
```