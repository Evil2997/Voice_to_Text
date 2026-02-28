# Voice → Text CLI (faster-whisper)

Современный CLI-инструмент для высококачественной транскрибации аудио/видео в текст на базе **faster-whisper**. 

Поддерживает два режима:
- **PROD** — быстрая практическая транскрипция одного файла с надёжным кешем.
- **BENCH** — полный перебор матрицы параметров (compute, threads, workers, beam, patience, vad), автоматический скоринг WER/CER и выбор лучшей конфигурации по точности → скорости.

Проект реализован по принципам **Clean Architecture**: Domain ← Application ← Infrastructure. Все зависимости инвертированы через порты, composition root находится в CLI-entrypoint.

---

### Возможности

- Поддержка локальных файлов и YouTube-ссылок (через yt-dlp)
- Автоматическая нормализация аудио → 16 kHz mono PCM WAV (ffmpeg)
- Строгий детерминированный кеш на основе `run_key`
- SQLite-репозиторий (runs.sqlite / bench.sqlite) для метрик и кеша
- BENCH: генерация матрицы параметров, устойчивость к падениям, Ctrl+C
- BENCH: скоринг WER/CER через jiwer (при наличии ref.txt)
- BENCH: автоматический выбор лучшей конфигурации
- Полная логика в домене, инфраструктура — только адаптеры
- Поддержка CPU (int8/float16) и CUDA

---

### Архитектура и слои

```text
Domain          ← Application     ← Infrastructure
(models,        (prod_service,    (sqlite_repo,
 ports,          bench_service,    whisper_engine,
 run_logic)      matrix, scoring)  target_preparer, ...)
```

- **Domain** владеет контрактами (`RunRepository`, `TranscribeEngine`, `TargetPreparer`).
- **Application** оркестрирует бизнес-сценарии.
- **Infrastructure** предоставляет конкретные реализации.
- **CLI** — единственная точка сборки зависимостей (composition root).

---

### Требования

**Python**: 3.12+

**Системные утилиты** (должны быть в PATH):
- `ffmpeg` + `ffprobe`
- `yt-dlp` (только для YouTube-ссылок)

**Python-зависимости**:
```bash
uv pip install faster-whisper jiwer pydantic pydantic-settings
```

---

### Установка

```bash
git clone https://github.com/yourname/voice-to-text-cli.git
cd voice-to-text-cli

# Рекомендуется uv
uv sync          # или uv pip install -e .
uv run python main.py --help
```

---

### Быстрый старт

#### PROD-режим (практическая транскрипция)

```bash
# Локальный файл
uv run python main.py --mode prod --target ./my_audio.mp3 --out-dir ./out

# YouTube
uv run python main.py --mode prod --target "https://youtu.be/..." --out-dir ./out
```

#### BENCH-режим (бенчмарк)

```bash
uv run python main.py --mode bench \
  --target ./my_audio.mp3 \
  --out-dir ./out \
  --bench.sample-seconds 60 \
  --bench.ref ./ref.txt
```

Пример переопределения матрицы:

```bash
uv run python main.py --mode bench \
  --target ./audio.wav \
  --bench.threads 4,8,12 \
  --bench.beams 1,5,10 \
  --bench.vads false,true \
  --bench.ref ./ref.txt
```

---

### Конфигурация

Настройки читаются в порядке приоритета:
1. CLI-аргументы (`--whisper.threads 12`)
2. Переменные окружения (`VOICE2TEXT__WHISPER__THREADS=12`)
3. Значения по умолчанию

**Примеры ENV**:

```bash
export VOICE2TEXT__MODE=bench
export VOICE2TEXT__TARGET=/path/to/audio.wav
export VOICE2TEXT__OUT_DIR=./results
export VOICE2TEXT__WHISPER__MODEL=large-v3
export VOICE2TEXT__BENCH__SAMPLE_SECONDS=90
```

Полный список параметров — в `voice_to_text__app/infrastructure/config/settings.py`.

---

### Выходные артефакты (`out_dir`)

```
out/
├── prepared/               # нормализованные 16k mono WAV
├── sample/                 # сэмплы для BENCH (если включён)
├── *.txt                   # результаты транскрипции
├── runs.sqlite             # PROD (или bench.sqlite)
└── (для BENCH) wer/cer обновляются в БД
```

---

### Кеширование и детерминизм

Ключ кеша (`run_key`) формируется из:
`target_id | model | device | compute_type | thr= | wrk= | beam= | pat= | vad= | lang=`

**Строгий кеш** считается валидным, только если:
- файл `.txt` существует
- запись с этим `run_key` присутствует в SQLite

---

### BENCH: выбор лучшей конфигурации

Алгоритм `pick_best`:
1. Игнорирует `failed` прогоны
2. Если есть WER/CER → сортировка: **WER → CER → wall_time → RTF**
3. Если скоринга нет → **wall_time → RTF**

Результат выводится в лог в конце бенча.

---

### Известные нюансы

- VAD работает, но на некоторых системах может потребовать дополнительных onnxruntime зависимостей.
- При смене `--bench.sample-seconds` старые сэмплы не переиспользуются (новый target_id).
- BENCH всегда использует `device=cpu` (как задумано в матрице).
- `jiwer` требуется только при `--bench.ref`.

---

### Project layout

```
voice_to_text__app/
├── domain/              # модели, исключения, run_logic, порты
├── application/
│   ├── bench/           # bench_service, matrix, scoring, selection
│   └── prod/            # prod_service
├── infrastructure/
│   ├── audio/           # targets, media, process (ffmpeg/yt-dlp)
│   ├── cli/             # entrypoint, logging, cli_source
│   ├── config/          # settings, pydantic-settings
│   ├── sqlite/          # schema + SqliteRunRepository
│   └── whisper/         # WhisperEngine (lifecycle)
├── main.py
├── pyproject.toml
└── uv.lock
```

---

### Дорожная карта (Roadmap)

- [ ] Полная поддержка extras в pyproject.toml (faster-whisper, jiwer)
- [ ] Интеграция в больший AI-пайплайн (Telegram → RabbitMQ → Worker → LLM-postprocessing)
- [ ] Docker-образ и GitHub Actions
- [ ] Поддержка batch-режима и Postgres (опционально)
- [ ] Версионирование транскриптов + постобработка LLM

Текущая версия — стабильная архитектурная основа (Stage 4 по внутренним SSD-документам).

---

### Лицензия

TBD (MIT / Apache 2.0 — выберите при публикации)

---

### Разработка

```bash
uv sync --dev          # если добавите dev-зависимости
uv run ruff check .    # (при наличии ruff)
uv run python main.py --mode bench --target ... 
```

Pull-request'ы приветствуются. Перед отправкой убедитесь, что:
- тесты проходят (пока тестов нет — планируются)
- код соответствует структуре слоёв
- новые фичи проходят через порты домена

---

**Готовы к использованию в продакшен-пайплайнах и исследовательским бенчмаркам.**  
Звёздочка на GitHub очень мотивирует ❤️

---

*Проект развивался поэтапно (см. исторические SSD__*.md в репозитории). Текущая версия — чистая, расширяемая архитектурная система.*