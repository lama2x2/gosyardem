"""Сборка и жизненный цикл Telegram-бота (запуск вместе с FastAPI)."""

import logging
from typing import Optional

from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from app.config import settings
from app.bot.handlers import (
    start,
    help_cmd,
    my_requests,
    create_request_start,
    handle_create_request_text,
    handle_request_photo,
    skip_photo,
)
from app.bot.staff_handlers import callback_handler

logger = logging.getLogger(__name__)

_bot_application: Optional[Application] = None


def get_bot_application() -> Optional[Application]:
    return _bot_application


async def _error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.exception("Ошибка в обработчике бота", exc_info=context.error)


def build_application() -> Optional[Application]:
    token = settings.telegram_bot_token
    if not token:
        logger.warning("TELEGRAM_BOT_TOKEN не задан — бот не запускается.")
        return None

    app = (
        Application.builder()
        .token(token)
        .connect_timeout(30.0)
        .read_timeout(30.0)
        .write_timeout(30.0)
        .pool_timeout(30.0)
        .build()
    )
    app.add_error_handler(_error_handler)

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("list", my_requests))
    app.add_handler(CommandHandler("new", create_request_start))
    app.add_handler(CommandHandler("skip", skip_photo))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.PHOTO, handle_request_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_create_request_text))

    return app


async def start_bot() -> None:
    global _bot_application
    if _bot_application is not None:
        return

    application = build_application()
    if application is None:
        return

    try:
        await application.initialize()
        await application.start()
        await application.updater.start_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True,
        )
        _bot_application = application
        logger.info("Telegram-бот запущен (polling).")
    except Exception:
        logger.exception("Не удалось запустить Telegram-бота — API продолжит работу.")
        try:
            await application.shutdown()
        except Exception:
            pass


async def stop_bot() -> None:
    global _bot_application
    application = _bot_application
    _bot_application = None
    if application is None:
        return

    try:
        if application.updater.running:
            await application.updater.stop()
        await application.stop()
        await application.shutdown()
        logger.info("Telegram-бот остановлен.")
    except Exception:
        logger.exception("Ошибка при остановке Telegram-бота.")
