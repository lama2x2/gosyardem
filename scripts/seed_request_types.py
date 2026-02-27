"""
Сид типов заявок (заглушка под зоны ответственности).
Запуск: python -m scripts.seed_request_types
"""

import asyncio
import sys

sys.path.insert(0, ".")

from sqlalchemy import select
from app.database import async_session_factory
from app.models import RequestType


DEFAULT_TYPES = [
    {"name": "Дороги и тротуары", "slug": "roads"},
    {"name": "ЖКХ", "slug": "housing"},
    {"name": "Освещение", "slug": "lighting"},
    {"name": "Другое", "slug": "other"},
]


async def seed() -> None:
    async with async_session_factory() as session:
        for item in DEFAULT_TYPES:
            result = await session.execute(select(RequestType).where(RequestType.slug == item["slug"]))
            if result.scalar_one_or_none():
                continue
            rt = RequestType(name=item["name"], slug=item["slug"])
            session.add(rt)
        await session.commit()
    print("Типы заявок созданы (или уже существуют).")


if __name__ == "__main__":
    asyncio.run(seed())
