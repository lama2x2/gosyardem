"""
Точка входа для Telegram-бота.
Запуск: python -m app.bot.run_bot (из корня проекта)
Токен берётся из TELEGRAM_BOT_TOKEN в .env.
"""

import logging

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

from app.config import settings
from app.bot.handlers import (
    start,
    help_cmd,
    my_requests,
    create_request_start,
    handle_create_request_text,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def main() -> None:
    token = settings.telegram_bot_token
    if not token:
        logger.warning("TELEGRAM_BOT_TOKEN не задан. Бот не запустится.")
        return

    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("list", my_requests))
    app.add_handler(CommandHandler("new", create_request_start))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_create_request_text)
    )

    logger.info("Бот запущен.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
