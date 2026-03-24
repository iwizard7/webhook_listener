# webhook_listener 🔮
![GitHub code size in bytes](https://img.shields.io/github/languages/code-size/iwizard7/webhook_listener) ![GitHub repo file count (file type)](https://img.shields.io/github/directory-file-count/iwizard7/webhook_listener)
[![Pylint](https://github.com/iwizard7/webhook_listener/actions/workflows/pylint.yml/badge.svg?branch=main)](https://github.com/iwizard7/webhook_listener/actions/workflows/pylint.yml) [![CodeQL](https://github.com/iwizard7/webhook_listener/actions/workflows/codeql.yml/badge.svg)](https://github.com/iwizard7/webhook_listener/actions/workflows/codeql.yml) [![Bandit](https://github.com/iwizard7/webhook_listener/actions/workflows/bandit.yml/badge.svg)](https://github.com/iwizard7/webhook_listener/actions/workflows/bandit.yml)

Webhook listener на Flask с базовым production-функционалом:
- прием JSON webhook на `POST /webhook` (и `POST /` для обратной совместимости);
- healthcheck endpoint `GET /healthz`;
- проверка HMAC-подписи (`X-Hub-Signature-256`) при заданном секрете;
- хранение событий в SQLite.

## Быстрый старт

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

Сервер запускается на `http://127.0.0.1:8000`.

## Конфигурация

Используются переменные окружения:
- `WEBHOOK_DB_PATH` (по умолчанию `data/webhooks.db`) - путь к SQLite БД;
- `WEBHOOK_SECRET` (по умолчанию пустой) - секрет для проверки подписи.

Если `WEBHOOK_SECRET` не задан, подпись не проверяется.

## Примеры запросов

Без подписи:

```bash
curl -i -X POST http://127.0.0.1:8000/webhook \
  -H "Content-Type: application/json" \
  -d '{"text":"hello"}'
```

С подписью (GitHub-стиль):

```bash
BODY='{"text":"signed"}'
SIG=$(printf '%s' "$BODY" | openssl dgst -sha256 -hmac "$WEBHOOK_SECRET" -hex | sed 's/^.* //')

curl -i -X POST http://127.0.0.1:8000/webhook \
  -H "Content-Type: application/json" \
  -H "X-Hub-Signature-256: sha256=$SIG" \
  -d "$BODY"
```

Проверка здоровья:

```bash
curl -i http://127.0.0.1:8000/healthz
```

## Локальная проверка

```bash
pytest
```
