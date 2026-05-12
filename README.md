# Voice → Text CLI

CLI-инструмент для транскрибации аудио и видео в текст на базе [faster-whisper](https://github.com/SYSTRAN/faster-whisper).

Поддерживает локальные файлы и YouTube-ссылки. Два режима работы: быстрая транскрибация (`prod`) и полный перебор параметров для поиска оптимальной конфигурации (`bench`).

---

## Возможности

- Локальные файлы и YouTube-ссылки (через `yt-dlp`)
- Автоматическая нормализация аудио → 16 kHz mono PCM WAV через `ffmpeg`
- Детерминированный кеш на основе `run_key` — повторный запуск с теми же параметрами не тратит время
- SQLite для хранения всех прогонов с метриками (wall time, RTF, WER, CER)
- `bench` режим: матрица параметров (threads × workers × beam × vad), скоринг WER/CER через jiwer, автовыбор лучшей конфигурации
- Clean Architecture: Domain ← Application ← Infrastructure, зависимости инвертированы через порты
- CLI без argparse — свой парсер с вложенными ключами (`--whisper.threads 8`)

---

## Стек

- **Python 3.12+**
- [faster-whisper](https://github.com/SYSTRAN/faster-whisper) — транскрибация
- [jiwer](https://github.com/jitsi/jiwer) — WER/CER скоринг (только для bench с ref)
- [Pydantic](https://docs.pydantic.dev/) + [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) — модели и конфиг
- [uv](https://github.com/astral-sh/uv) — управление зависимостями
- Системные утилиты: `ffmpeg`, `ffprobe`, `yt-dlp`

---

## Требования

```bash
# ffmpeg
sudo apt install ffmpeg

# yt-dlp (только для YouTube)
pip install yt-dlp
```

---

## Установка

```bash
git clone https://github.com/Evil2997/voice-to-text-cli.git
cd voice-to-text-cli
uv sync
```

---

## Использование

### PROD — транскрибация файла или URL

```bash
# Локальный файл
uv run python main.py --mode prod --target ./audio.mp3

# YouTube
uv run python main.py --mode prod --target "https://youtu.be/..."

# Переопределить модель и устройство
uv run python main.py --mode prod --target ./audio.mp3 \
  --whisper.model large-v3 \
  --whisper.device cpu \
  --whisper.threads 8
```

### BENCH — поиск лучшей конфигурации

```bash
# Базовый запуск (матрица по умолчанию)
uv run python main.py --mode bench --target ./audio.mp3 --bench.ref ./ref.txt

# Кастомная матрица
uv run python main.py --mode bench \
  --target ./audio.mp3 \
  --bench.threads 4,8,12 \
  --bench.beams 1,5,10 \
  --bench.sample-seconds 60 \
  --bench.ref ./ref.txt
```

`ref.txt` — эталонный текст для подсчёта WER/CER. Без него bench работает, но выбирает лучший конфиг только по скорости.

---

## Конфигурация

Приоритет: CLI-аргументы → переменные окружения → дефолты.

```bash
# Через ENV
export VOICE2TEXT__MODE=prod
export VOICE2TEXT__TARGET=/path/to/audio.wav
export VOICE2TEXT__WHISPER__MODEL=large-v3
export VOICE2TEXT__WHISPER__THREADS=8
export VOICE2TEXT__OUT_DIR=./workspace
```

Полный список параметров — в `voice_to_text__app/infrastructure/config/settings.py`.

---

## Структура рабочей директории

По умолчанию `./workspace` (настраивается через `--out-dir`):

```
workspace/
├── prepared/                        # нормализованные WAV (кеш)
├── sample/                          # сэмплы для bench
├── full_120__abc123.txt             # результат prod транскрибации
├── full_120_sample_120__def456.txt  # результаты bench прогонов
├── runs.sqlite                      # prod: история прогонов
└── bench.sqlite                     # bench: история прогонов + метрики
```

---

## Кеширование

Ключ кеша (`run_key`) включает: `target_id | model | device | compute_type | threads | workers | beam_size | patience | vad | lang`

Прогон считается кешированным если **и** `.txt` существует, **и** запись с этим `run_key` есть в SQLite. Оба условия обязательны.

---

## Структура проекта

```
voice_to_text__app/
├── domain/
│   ├── models.py           # PreparedTarget, TranscribeConfig, RunResult
│   ├── exceptions.py
│   ├── run_logic.py        # основная логика одного прогона
│   └── ports/
│       ├── run_repository.py    # Protocol: get / upsert / list_all
│       ├── transcribe_engine.py # Protocol: transcribe(wav, cfg)
│       └── target_preparer.py   # Protocol: prepare / make_sample
├── application/
│   ├── prod/
│   │   └── prod_service.py
│   └── bench/
│       ├── bench_service.py
│       ├── matrix.py       # генератор матрицы конфигов
│       ├── scoring.py      # WER/CER через jiwer
│       └── selection.py    # pick_best
├── infrastructure/
│   ├── audio/
│   │   ├── targets.py      # yt-dlp, нормализация WAV
│   │   ├── media.py        # ffprobe: длительность
│   │   ├── process.py      # run_cmd обёртка
│   │   └── target_preparer.py  # AudioTargetPreparer
│   ├── cli/
│   │   ├── entrypoint.py   # composition root
│   │   ├── cli_source.py   # парсер argv без argparse
│   │   └── logging.py
│   ├── config/
│   │   └── settings.py
│   ├── sqlite/
│   │   ├── schema.py
│   │   └── sqlite_repo.py
│   └── whisper/
│       └── whisper_engine.py  # lifecycle WhisperModel
└── main.py
```
