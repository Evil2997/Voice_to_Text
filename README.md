# Voice → Text CLI (faster-whisper)

CLI tool for speech-to-text transcription using **faster-whisper**.
Supports two modes:

- **PROD**: practical transcription (single run) with caching into CSV + `.txt`
- **BENCH**: benchmark matrix (compute/threads/workers/beam/patience/vad, etc.),
  optional WER/CER scoring with a reference text, and best config selection:
  **most accurate first, then fastest**

## Requirements

You need external tools installed:

- `ffmpeg` + `ffprobe`
- `yt-dlp` (only if you use YouTube URLs as targets)

Python deps:
- `faster-whisper`
- `pydantic`
- `pydantic-settings`
- `jiwer` (only used for bench scoring)

## Project structure

- `main_app/core/` — shared core (targets prep, runner, CSV store, external tools)
- `main_app/prod/` — prod module (transcribe + caching)
- `main_app/bench/` — bench module (matrix, scoring, best selection)
- `main_app/settings/` — `Settings()` (argv/env/defaults), no argparse
- `main_app/app/` — entrypoint + logging config

## Usage

### PROD mode

```bash
python main.py --mode prod --target /path/to/audio.mp3 --out-dir ./out
````

You can also use a YouTube URL:

```bash
python main.py --mode prod --target "https://youtu.be/..." --out-dir ./out
```

### BENCH mode

Minimal bench run:

```bash
python main.py --mode bench --target /path/to/audio.mp3 --out-dir ./out --bench.sample-seconds 60
```

Bench with scoring:

```bash
python main.py --mode bench --target /path/to/audio.mp3 --out-dir ./out \
  --bench.sample-seconds 60 \
  --bench.ref ./ref.txt
```

Override matrix parameters (comma-separated lists):

```bash
python main.py --mode bench --target /path/to/audio.mp3 --out-dir ./out \
  --bench.threads 4,8,12 \
  --bench.workers 1,2 \
  --bench.computes int8,float16 \
  --bench.beams 1,5,10 \
  --bench.patiences 1.0,1.2 \
  --bench.vads false,true
```

Override whisper settings:

```bash
python main.py --mode prod --target /path/to/audio.mp3 --out-dir ./out \
  --whisper.model large-v3 \
  --whisper.device cpu \
  --whisper.threads 10 \
  --whisper.workers 2 \
  --whisper.beam_size 10 \
  --whisper.patience 1.0 \
  --whisper.vad true \
  --whisper.lang auto
```

## Environment variables

All settings can be provided via env variables using prefix:

* `VOICE2TEXT__MODE`
* `VOICE2TEXT__TARGET`
* `VOICE2TEXT__OUT_DIR`
* `VOICE2TEXT__WHISPER__THREADS`
* `VOICE2TEXT__BENCH__SAMPLE_SECONDS`

Nested delimiter is `__`.

Example:

```bash
export VOICE2TEXT__MODE=prod
export VOICE2TEXT__TARGET=/path/to/audio.mp3
export VOICE2TEXT__OUT_DIR=./out
export VOICE2TEXT__WHISPER__THREADS=12
python main.py
```

## Output files

In `--out-dir`:

* `prepared/` — normalized WAV 16k mono
* `runs.csv` — PROD results and cache index
* `bench_results.csv` — BENCH results and cache index
* `*.txt` — transcripts (one for prod, many for bench)
* `sample/` — bench samples (`*_sample_N.wav`)

## Notes

* PROD caching is strict: cached only if both `.txt` exists and the run key exists in CSV.
* BENCH uses the same strict caching logic per configuration.
* `jiwer` is only used when `--bench.ref` exists.

