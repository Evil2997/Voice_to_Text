# Voice → Text CLI

CLI tool for transcribing audio and video to text using [faster-whisper](https://github.com/SYSTRAN/faster-whisper).

Supports local files and YouTube URLs. Two modes: fast single-file transcription (`prod`) and full parameter matrix search for finding the optimal Whisper configuration (`bench`).

---

## What it does

- Local files and YouTube URLs (via `yt-dlp`)
- Automatic audio normalization → 16 kHz mono PCM WAV via `ffmpeg`
- Deterministic cache based on `run_key` — same file with same parameters never runs twice
- SQLite for storing all runs with metrics (wall time, RTF, WER, CER)
- `bench` mode: parameter matrix (threads × workers × beam × vad), WER/CER scoring via jiwer, automatic best-config selection
- **Structured output**: every run produces `.txt`, `.json` (with timestamps), `.srt` and `.vtt` subtitle files
- **Chunking**: split transcripts into logical blocks by pause, time window, or word count
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
uv sync --extra whisper
```

---

## Usage

### PROD — transcribe a file or URL

```bash
# Local file
uv run v2t --mode prod --target ./audio.mp3

# YouTube
uv run v2t --mode prod --target "https://youtu.be/..."

# Override model and device
uv run v2t --mode prod --target ./audio.mp3 \
  --whisper.model large-v3 \
  --whisper.device cpu \
  --whisper.threads 8
```

### BENCH — find the best configuration

```bash
# Default matrix
uv run v2t --mode bench --target ./audio.mp3 --bench.ref ./ref.txt

# Custom matrix
uv run v2t --mode bench \
  --target ./audio.mp3 \
  --bench.threads 4,8,12 \
  --bench.beams 1,5,10 \
  --bench.sample-seconds 60 \
  --bench.ref ./ref.txt
```

`ref.txt` is the reference transcript for WER/CER scoring. Without it bench still runs but selects the best config by speed only.

---

## Output formats

Every transcription run produces four files side by side:

| File | Content |
|---|---|
| `<name>.txt` | Plain text transcript |
| `<name>.json` | Structured transcript with segment timestamps |
| `<name>.srt` | SubRip subtitles |
| `<name>.vtt` | WebVTT subtitles |

Example `.json` output:

```json
{
  "segments": [
    { "start": 0.0, "end": 3.2, "text": "Hello, how are you?" },
    { "start": 3.5, "end": 7.1, "text": "I wanted to discuss the project." }
  ],
  "language": "en",
  "duration_sec": 7.1
}
```

---

## Chunking

Split a transcript into logical blocks without any AI — pure algorithmic, based on segment boundaries already provided by Whisper.

Three strategies:

| Strategy | Parameter | Description |
|---|---|---|
| `pause` | `min_pause_sec` (default: 1.5s) | New chunk on silence gap between segments |
| `time` | `window_sec` (default: 30s) | Fixed time windows |
| `words` | `max_words` (default: 100) | Fixed word count windows |

```python
from voice_to_text__app.domain.chunking import chunk_by_pause, chunk_by_time, chunk_by_words

chunks = chunk_by_pause(transcript, min_pause_sec=2.0)
chunks = chunk_by_time(transcript, window_sec=60)
chunks = chunk_by_words(transcript, max_words=150)

for chunk in chunks:
    print(f"[{chunk.start:.1f}s → {chunk.end:.1f}s] {chunk.text}")
```

Each chunk is a `TranscriptChunk` with `start`, `end`, `text`, `segment_count`.

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
├── audio.txt                        # plain text transcript
├── audio.json                       # structured transcript with timestamps
├── audio.srt                        # SubRip subtitles
├── audio.vtt                        # WebVTT subtitles
├── audio__<run_id>.txt              # bench results (one set per config)
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
│   ├── models.py                    # PreparedTarget, TranscribeConfig, Transcript, RunResult
│   ├── exceptions.py
│   ├── run_logic.py                 # single-run logic: cache, transcribe, persist
│   ├── chunking.py                  # chunk_by_pause / chunk_by_time / chunk_by_words
│   └── ports/
│       ├── run_repository.py        # Protocol: get / upsert / list_all
│       ├── transcribe_engine.py     # Protocol: transcribe(wav, cfg) -> Transcript
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