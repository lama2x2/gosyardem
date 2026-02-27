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

## Локальный запуск (без Docker)

1. Создать виртуальное окружение и установить зависимости:

```bash
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

2. Поднять PostgreSQL и задать в `.env`:

- `DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/citizen_support`
- `DATABASE_URL_SYNC=postgresql://user:password@localhost:5432/citizen_support`

3. Применить миграции:

```bash
alembic upgrade head
```

4. Запустить приложение:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

5. (Опционально) Запустить бота (нужен `TELEGRAM_BOT_TOKEN` в `.env`):

```bash
python -m app.bot.run_bot
```

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
