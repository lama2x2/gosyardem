"""
Обработчики Telegram-бота.
Вся логика работы — в телеге; бот дергает API бэкенда (FastAPI).
"""

import logging
from typing import Optional

from telegram import Message, Update
from telegram.ext import ContextTypes
from telegram.error import TelegramError

from app.bot import api_client
from app.bot.notify import notify_user_id
from app.bot.profile import display_name_from_telegram, sync_profile
from app.bot.staff_handlers import (
    handle_proof_comment_text,
    handle_proof_photo,
    handle_rating_review_text,
    role_help,
    send_request_list,
    skip_proof_photo,
    skip_rating_review,
)
from app.labels import request_status_ru

logger = logging.getLogger(__name__)


async def safe_reply(message: Optional[Message], text: str) -> None:
    if not message:
        return
    try:
        await message.reply_text(text)
    except TelegramError:
        logger.exception("Не удалось отправить сообщение в Telegram")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not user or not update.message:
        return
    await sync_profile(update)
    me = await api_client.get_user_by_telegram_id(user.id)
    if not me:
        me = await api_client.register_citizen(user.id, display_name_from_telegram(user))
        if me:
            await safe_reply(
                update.message,
                "Добро пожаловать! Вы зарегистрированы как гражданин.\n"
                "Используйте /new для создания заявки, /list — для просмотра.\n"
                "/help — справка.",
            )
            return
        await safe_reply(
            update.message,
            "Не удалось зарегистрироваться. Если вы оператор или исполнитель — "
            "учётная запись должна быть создана администратором с вашим Telegram ID.",
        )
        return

    role = me["role"]
    if role == "citizen":
        text = (
            "С возвращением! /new — новая заявка, /list — мои заявки, /help — справка."
        )
    elif role == "operator":
        text = (
            "С возвращением, оператор! /list — заявки с фото и назначением исполнителей, "
            "/help — справка."
        )
    elif role == "executor":
        text = (
            "С возвращением, исполнитель! /list — ваши заявки, пруфы и статусы. /help — справка."
        )
    else:
        text = "С возвращением! /list — заявки, /help — справка."
    await safe_reply(update.message, text)


NEW_REQUEST_INTRO = (
    "Создание заявки — 4 шага:\n"
    "1️⃣ Название — коротко, в чём проблема (например: «Яма на дороге»).\n"
    "2️⃣ Адрес — где именно (улица, дом, подъезд, ориентир).\n"
    "3️⃣ Описание — подробности: размер, давность, опасность и т.п.\n"
    "4️⃣ Фото — снимок проблемы или /skip, если фото нет.\n\n"
    "Шаг 1 из 4. Введите название:"
)


async def create_request_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await sync_profile(update)
    me = await api_client.get_user_by_telegram_id(
        update.effective_user.id if update.effective_user else 0
    )
    if not me or me["role"] != "citizen":
        await safe_reply(update.message, "Создавать заявки могут только граждане.")
        return
    await safe_reply(update.message, NEW_REQUEST_INTRO)
    context.user_data["creating_request"] = {"step": "title"}


async def create_request_title(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.user_data.get("creating_request", {}).get("step") != "title":
        return
    context.user_data["creating_request"]["title"] = update.message.text
    context.user_data["creating_request"]["step"] = "address"
    await safe_reply(
        update.message,
        "Шаг 2 из 4. Укажите адрес (улица, дом, подъезд или ориентир):",
    )


async def create_request_address(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.user_data.get("creating_request", {}).get("step") != "address":
        return
    context.user_data["creating_request"]["address"] = update.message.text
    context.user_data["creating_request"]["step"] = "description"
    await safe_reply(
        update.message,
        "Шаг 3 из 4. Опишите проблему подробнее (что именно не так):",
    )


async def handle_create_request_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await sync_profile(update)
    if await handle_proof_comment_text(update, context):
        return
    if await handle_rating_review_text(update, context):
        return
    step = context.user_data.get("creating_request", {}).get("step")
    if step == "title":
        await create_request_title(update, context)
    elif step == "address":
        await create_request_address(update, context)
    elif step == "description":
        await create_request_description(update, context)


async def create_request_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    data = context.user_data.get("creating_request")
    if not data or data.get("step") != "description":
        return
    data["description"] = update.message.text or ""
    data["step"] = "photo"
    await safe_reply(
        update.message,
        "Шаг 4 из 4. Отправьте фото проблемы или /skip, чтобы создать заявку без фото.",
    )


async def handle_request_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await sync_profile(update)
    if await handle_proof_photo(update, context):
        return
    data = context.user_data.get("creating_request")
    if not data or data.get("step") != "photo":
        return
    if not update.message or not update.message.photo:
        return
    data["photo_file_id"] = update.message.photo[-1].file_id
    await finalize_request(update, context)


async def skip_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.user_data.get("uploading_proof"):
        await skip_proof_photo(update, context)
        return
    if context.user_data.get("rating_request"):
        await skip_rating_review(update, context)
        return
    data = context.user_data.get("creating_request")
    if not data or data.get("step") != "photo":
        await safe_reply(
            update.message,
            "Команда /skip: фото заявки (шаг 4), фото пруфа (шаг 2) или отзыв.",
        )
        return
    await finalize_request(update, context)


async def finalize_request(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    data = context.user_data.get("creating_request")
    if not data:
        return

    title = data.get("title", "")
    address = data.get("address", "")
    description = data.get("description", "")
    photo_file_id = data.get("photo_file_id")
    telegram_id = update.effective_user.id if update.effective_user else 0

    citizen = await api_client.get_user_by_telegram_id(telegram_id)
    if not citizen:
        await safe_reply(update.message, "Вы не зарегистрированы. Нажмите /start для регистрации.")
        context.user_data.pop("creating_request", None)
        return

    payload = {
        "user_id": citizen["id"],
        "title": title,
        "description": description,
        "address": address or None,
        "type_id": None,
        "photo_file_id": photo_file_id,
    }

    req = await api_client.create_request(payload)
    context.user_data.pop("creating_request", None)
    if not req:
        await safe_reply(update.message, "Не удалось создать заявку. Попробуйте позже.")
        return

    photo_note = " Фото прикреплено." if req.get("photo_file_id") else ""
    await safe_reply(
        update.message,
        f"Заявка №{req['id']} создана. Статус: {request_status_ru(req['status'])}.{photo_note} "
        "Вы получите уведомление при изменении.",
    )
    if req.get("assigned_operator_id"):
        await notify_user_id(
            req["assigned_operator_id"],
            f"Новая заявка №{req['id']}: {req['title']}.",
            req.get("photo_file_id"),
            request_id=req["id"],
        )


async def my_requests(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await sync_profile(update)
    telegram_id = update.effective_user.id if update.effective_user else 0
    me = await api_client.get_user_by_telegram_id(telegram_id)
    if not me:
        await safe_reply(update.message, "Пользователь не найден. Нажмите /start.")
        return
    if not update.message:
        return
    await send_request_list(update.message, me, context)


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await sync_profile(update)
    telegram_id = update.effective_user.id if update.effective_user else 0
    me = await api_client.get_user_by_telegram_id(telegram_id)
    role = me["role"] if me else "citizen"
    await safe_reply(update.message, role_help(role))
