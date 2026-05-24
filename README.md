# Платформа помощи гражданам (gosyardem)

Сервис для приёма и обработки обращений граждан по городским проблемам. Фронт — Telegram-бот, бэкенд — FastAPI + SQLAlchemy + PostgreSQL.

## Стек

- **Backend:** FastAPI, SQLAlchemy (async), PostgreSQL
- **Документация API:** Swagger UI — `/docs`, ReDoc — `/redoc`
- **Админка:** SQLAdmin — `/admin`
- **Бот:** python-telegram-bot, общается с API бэкенда

## Запуск через Docker

```bash
docker-compose up --build
```

API: http://localhost:8000  
Swagger: http://localhost:8000/docs  
Админка: http://localhost:8000/admin  

Telegram-бот стартует **вместе с API** (нужен `TELEGRAM_BOT_TOKEN` в `.env`).  
При ошибках бота API продолжает работать.

## Локальный запуск (без Docker)

1. Создать виртуальное окружение и установить зависимости:

```bash
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

2. Поднять PostgreSQL и задать в `.env` (URL собирается в коде из переменных):

- `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`
- `POSTGRES_HOST=localhost` при запуске API на хосте; при запуске через Docker в `.env` должен быть хост БД в сети compose — здесь `POSTGRES_HOST=db` (имя сервиса `db` в `docker-compose.yml`), порт `5432`

3. Применить миграции:

```bash
alembic upgrade head
```

4. Запустить приложение:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

5. Указать `TELEGRAM_BOT_TOKEN` в `.env` — бот запустится вместе с API.

   Отдельный запуск бота (только для отладки):

```bash
python -m app.bot.run_bot
```

   Создание заявки в боте: `/new` → название → адрес → описание → фото или `/skip`.

## Скрипты

- **Суперпользователь** (логин, пароль, Telegram ID):

```bash
python -m scripts.create_superuser --username admin --password admin --telegram-id 123456789
```

- **Сид типов заявок** (заглушка под зоны ответственности):

```bash
python -m scripts.seed_request_types
```

## Документация для научрука

Описание проекта, пользовательские сценарии и глоссарий терминов: [docs/project_description.md](docs/project_description.md).
