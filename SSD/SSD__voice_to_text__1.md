# Voice → Text CLI — Project State (Stage 4)

## Общая цель проекта

CLI-инструмент для транскрибации аудио/видео в текст на базе faster-whisper.

Проект разделён на:

* CORE — общее ядро (подготовка аудио, запуск whisper, CSV, кеш, инструменты)
* PROD — практическая транскрибация (один запуск + строгий кеш)
* BENCH — перебор матрицы параметров, скоринг WER/CER, выбор best

Запуск из CLI, но без argparse — через Settings().

---

# Архитектура проекта

## Структура

main_app/

* core/
* prod/
* bench/
* settings/
* app/

main.py — entrypoint

---

# CORE

Отвечает за:

* Подготовку target (локальный файл или URL)
* Скачивание через yt-dlp
* Нормализацию аудио в WAV 16k mono PCM (ffmpeg)
* Запуск faster-whisper
* Подсчёт метрик (wall time, RTF)
* Работа с CSV
* Генерация run_key
* Кеширование

### Правила

* Whisper получает **только нормализованный WAV**
* Формат WAV:

  * mono
  * 16 kHz
  * pcm_s16le
* run_key стабилен
* bench naming использует sha1(run_key)

---

# Подготовка target (универсальный pipeline)

Если target = URL:

* yt-dlp скачивает bestaudio
* сохраняется в out/downloads/src_<id>.<ext>

Любой raw файл:

* нормализуется в out/prepared/<basename>__<target_id>.wav
* если уже существует — используется кеш

---

# Whisper

* device: cpu
* compute_type: int8
* language: auto (никогда принудительно не задаётся)
* vad: false (в bench отключён из-за onnxruntime проблемы)

В коде:

language = None if cfg.lang == "auto" else cfg.lang

---

# PROD модуль

* Один прогон
* Строгий кеш:

  * txt существует
  * run_key есть в CSV
* Если ошибка — падает

---

# BENCH модуль

* Генерирует матрицу параметров
* CPU-only
* compute = int8
* vad = False
* Каждая комбинация:

  * либо cached
  * либо executed
  * либо failed
* failed не ломают bench
* CSV содержит status (ok/failed) + error
* Best выбирается:

  * если есть WER → минимальный WER → CER → wall → RTF
  * иначе → wall → RTF
* failed строки игнорируются при выборе best

---

# Логирование

Все print удалены.
Используется logging.

Уровни:

* info — основной прогресс
* warning — проблемы, пропуски, ошибки конфигураций
* error — фатальные

---

# Settings()

* Без argparse
* Читает:

  * CLI (--param value)
  * ENV (VOICE2TEXT__...)
  * Defaults
* Иерархия:

  * settings.mode
  * settings.target
  * settings.out_dir
  * settings.whisper.*
  * settings.bench.*

---

# Устойчивость

* Если VAD падает (onnxruntime issue) — bench продолжает
* Все failed прогоны фиксируются в CSV
* run_key детерминированный
* naming стабильный (без hash())

---

# Текущий статус

✔ Универсальный pipeline (URL → WAV → Whisper)
✔ CPU / int8 режим
✔ Автоопределение языка
✔ Строгое кеширование
✔ Bench устойчив к ошибкам
✔ CSV хранит статус выполнения
✔ Архитектура разделена по модулям
✔ Logging вместо print
✔ README добавлен

---

# Известные нюансы

* Если bench sample_seconds меняется, необходимо корректное именование sample (кеш должен учитывать seconds)
* onnxruntime не используется (VAD отключён)
* Whisper large-v3 на CPU работает медленно (RTF > 1 возможен)

---

# Рекомендуемый рабочий pipeline

1. Скачать видео:
   python main.py --mode prod --target "URL" --out-dir ./out

2. Автоматически:

   * yt-dlp → bestaudio
   * ffmpeg → 16k mono wav
   * whisper → txt
   * csv кеш

3. Текст → LLM обработка

---

# Архитектурная философия

* Простота
* Детерминизм
* Явное кеширование
* Чистый поток данных
* Минимум магии
* Логи вместо хаоса
* Бенч отделён от прод-логики

---

# Текущий этап = стабильная основа

Теперь проект:

* не MVP
* не скрипт
* а оформленный CLI-инструмент с модульной архитектурой

Готов к:

* публикации на GitHub
* упаковке через pyproject
* дальнейшему расширению

---

Если хочешь, следующим шагом можем:

* сделать версию v0.1.0
* оформить pyproject
* добавить CLI-имя (v2t)
* добавить pre-commit (ruff + formatting)
* или перейти к модулю LLM-постпроцессинга текста

Но на текущем этапе — архитектурно всё аккуратно и стабильно.
