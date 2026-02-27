"""
Создание суперпользователя: логин, пароль, telegram_id.
Запуск из корня проекта:
  python -m scripts.create_superuser
Или с аргументами:
  python -m scripts.create_superuser --username admin --password secret --telegram-id 123456789
"""

import asyncio
import argparse
import sys
from typing import Optional

# Добавляем корень проекта в path
sys.path.insert(0, ".")

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_factory
from app.models import User
from app.models.user import UserRole, UserSource
from app.auth import get_password_hash


async def create_superuser(username: str, password: str, telegram_id: Optional[int]) -> None:
    async with async_session_factory() as session:
        result = await session.execute(select(User).where(User.username == username))
        existing = result.scalar_one_or_none()
        if existing:
            print(f"Пользователь с логином {username} уже существует.")
            return
        user = User(
            username=username,
            password_hash=get_password_hash(password),
            role=UserRole.superuser,
            source=UserSource.telegram,
            telegram_id=telegram_id,
        )
        session.add(user)
        await session.commit()
        print(f"Суперпользователь создан: {username}, telegram_id={telegram_id}")


def main():
    parser = argparse.ArgumentParser(description="Создать суперпользователя")
    parser.add_argument("--username", "-u", default="admin", help="Логин")
    parser.add_argument("--password", "-p", default="admin", help="Пароль")
    parser.add_argument("--telegram-id", "-t", type=int, default=None, help="Telegram ID для привязки")
    args = parser.parse_args()
    asyncio.run(create_superuser(args.username, args.password, args.telegram_id))


if __name__ == "__main__":
    main()
