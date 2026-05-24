"""
Отдельный запуск бота (без FastAPI).
Обычно бот стартует вместе с API; эта точка входа — для отладки.
"""

import asyncio
import logging

from app.config import settings
from app.bot.app_factory import start_bot, stop_bot

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)


async def _run() -> None:
    if not settings.telegram_bot_token:
        logging.warning("TELEGRAM_BOT_TOKEN не задан.")
        return
    await start_bot()
    try:
        while True:
            await asyncio.sleep(3600)
    finally:
        await stop_bot()


def main() -> None:
    asyncio.run(_run())


if __name__ == "__main__":
    main()
