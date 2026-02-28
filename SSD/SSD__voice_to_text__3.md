# 📌 Voice → Text CLI — итог текущей сессии

## 1️⃣ Архитектура зафиксирована

### Направление зависимостей:

```
Domain ← Application ← Infrastructure
```

### Composition root:

* Единственная точка сборки зависимостей — `CLI entrypoint`
* Repo / Engine / TargetPreparer создаются там

---

## 2️⃣ Введены доменные порты

Созданы порты в `domain/ports`:

* `RunRepository`
* `TranscribeEngine`
* `TargetPreparer`

Domain больше не зависит от:

* SQLite
* Whisper
* ffmpeg / yt-dlp

Это завершает слой разделения.

---

## 3️⃣ Bench работает корректно и устойчиво

* WhisperEngine переиспользуется
* Двухуровневый кеш:

  * WAV preparation cache
  * strict run_key + DB cache
* Ctrl+C → graceful shutdown
* Bench устойчив к ошибкам

---

## 4️⃣ Run-key = строгий детерминизм

`run_key = target_id + model + device + compute + parameters`

Кеш считается валидным если:

* TXT существует
* запись в DB существует

Это жёсткая и правильная модель.

---

## 5️⃣ Статус проекта

Проект перешёл из “утилиты” в **архитектурную систему**:

* Слои отделены
* Порты введены
* Зависимости инвертированы
* Engine lifecycle контролируется
* Persistence абстрагирован

Это production-ready CLI.

---

# 🚀 Дальнейшее направление

## Интеграция в PDFnik

* Только Prod-use-case переносится
* Bench остаётся в текущем репозитории
* Telegram → RabbitMQ → Worker → Transcribe → Ответ
* Redis для кеша и контроля задач
* Контроль CPU/RAM перед запуском jobs

Идея: сделать Telegram-driven processing engine.

---

# 🧠 Главные выводы сессии

1. Архитектурные слои закреплены правильно.
2. Контракты принадлежат потребителю (Domain).
3. Composition root должен быть один.
4. Кеш реализован строго и детерминированно.
5. Проект готов стать частью многостадийного пайплайна.

---

# 🎯 Текущий этап можно считать завершённым

Voice → Text CLI:

* стабилен
* структурирован
* расширяем
* готов к интеграции
