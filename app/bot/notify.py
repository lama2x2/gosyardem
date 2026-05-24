"""Уведомления пользователей в Telegram (из обработчиков бота)."""

from __future__ import annotations

import logging
from typing import Optional

from telegram.error import TelegramError

from app.bot import api_client
from app.bot.keyboards import open_request_alert_keyboard

logger = logging.getLogger(__name__)


async def notify_user_id(
    user_id: int,
    text: str,
    photo_file_id: Optional[str] = None,
    *,
    request_id: Optional[int] = None,
) -> None:
    user = await api_client.get_user(user_id)
    if not user or not user.get("telegram_id"):
        return
    reply_markup = open_request_alert_keyboard(request_id) if request_id else None
    await notify_telegram(user["telegram_id"], text, photo_file_id, reply_markup=reply_markup)


async def notify_telegram(
    telegram_id: int,
    text: str,
    photo_file_id: Optional[str] = None,
    *,
    reply_markup=None,
) -> None:
    from app.bot.app_factory import get_bot_application

    application = get_bot_application()
    if application is None:
        return
    bot = application.bot
    try:
        if photo_file_id:
            await bot.send_photo(
                chat_id=telegram_id,
                photo=photo_file_id,
                caption=text[:1024],
                reply_markup=reply_markup,
            )
        else:
            await bot.send_message(
                chat_id=telegram_id,
                text=text,
                reply_markup=reply_markup,
            )
    except TelegramError:
        logger.exception("Не удалось уведомить telegram_id=%s", telegram_id)
