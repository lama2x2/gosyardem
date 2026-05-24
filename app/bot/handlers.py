"""
Обработчики Telegram-бота.
Вся логика работы — в телеге; бот дергает API бэкенда (FastAPI).
"""

import logging
from typing import Optional

import httpx
from telegram import Message, Update
from telegram.ext import ContextTypes
from telegram.error import TelegramError

from app.config import settings
from app.labels import request_status_ru

logger = logging.getLogger(__name__)

API_BASE = f"{settings.api_base_url.rstrip('/')}/api"


async def safe_reply(message: Optional[Message], text: str) -> None:
    if not message:
        return
    try:
        await message.reply_text(text)
    except TelegramError:
        logger.exception("Не удалось отправить сообщение в Telegram")


async def get_user_by_telegram_id(telegram_id: int) -> Optional[dict]:
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.get(f"{API_BASE}/users/by-telegram/{telegram_id}")
            if r.status_code != 200:
                return None
            return r.json()
    except httpx.HTTPError:
        logger.exception("Ошибка API при поиске пользователя")
        return None


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not user or not update.message:
        return
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.get(f"{API_BASE}/users/by-telegram/{user.id}")
            if r.status_code == 404:
                reg = await client.post(
                    f"{API_BASE}/users/",
                    json={"telegram_id": user.id, "role": "citizen"},
                )
                if reg.status_code in (200, 201):
                    await safe_reply(
                        update.message,
                        "Добро пожаловать! Вы зарегистрированы как гражданин. "
                        "Используйте /new для создания заявки, /list — для просмотра заявок.",
                    )
                    return
            elif r.status_code == 200:
                await safe_reply(
                    update.message,
                    "С возвращением! Используйте /new для заявки, /list — мои заявки, /help — справка.",
                )
                return
    except httpx.HTTPError:
        logger.exception("Ошибка API при регистрации")
    await safe_reply(
        update.message,
        "Платформа помощи гражданам. Используйте /help для списка команд.",
    )


NEW_REQUEST_INTRO = (
    "Создание заявки — 4 шага:\n"
    "1️⃣ Название — коротко, в чём проблема (например: «Яма на дороге»).\n"
    "2️⃣ Адрес — где именно (улица, дом, подъезд, ориентир).\n"
    "3️⃣ Описание — подробности: размер, давность, опасность и т.п.\n"
    "4️⃣ Фото — снимок проблемы или /skip, если фото нет.\n\n"
    "Шаг 1 из 4. Введите название:"
)


async def create_request_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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
    data = context.user_data.get("creating_request")
    if not data or data.get("step") != "photo":
        return
    if not update.message or not update.message.photo:
        return
    data["photo_file_id"] = update.message.photo[-1].file_id
    await finalize_request(update, context)


async def skip_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    data = context.user_data.get("creating_request")
    if not data or data.get("step") != "photo":
        await safe_reply(
            update.message,
            "Команда /skip доступна только на шаге 4 — когда бот просит фото.",
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

    citizen = await get_user_by_telegram_id(telegram_id)
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

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(f"{API_BASE}/requests/", json=payload)
    except httpx.HTTPError:
        logger.exception("Ошибка API при создании заявки")
        await safe_reply(update.message, "Не удалось создать заявку. Попробуйте позже.")
        context.user_data.pop("creating_request", None)
        return

    context.user_data.pop("creating_request", None)
    if r.status_code in (200, 201):
        req = r.json()
        photo_note = " Фото прикреплено." if req.get("photo_file_id") else ""
        await safe_reply(
            update.message,
            f"Заявка №{req['id']} создана. Статус: {request_status_ru(req['status'])}.{photo_note} "
            "Вы получите уведомление при изменении.",
        )
    else:
        await safe_reply(update.message, "Не удалось создать заявку. Попробуйте позже.")


async def my_requests(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    telegram_id = update.effective_user.id if update.effective_user else 0
    me = await get_user_by_telegram_id(telegram_id)
    if not me:
        await safe_reply(update.message, "Пользователь не найден. Нажмите /start.")
        return
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            reqs_r = await client.get(f"{API_BASE}/requests/")
            if reqs_r.status_code != 200:
                await safe_reply(update.message, "Ошибка загрузки заявок.")
                return
            reqs = reqs_r.json()
    except httpx.HTTPError:
        logger.exception("Ошибка API при загрузке заявок")
        await safe_reply(update.message, "Ошибка загрузки заявок.")
        return

    if me["role"] == "citizen":
        my = [r for r in reqs if r["user_id"] == me["id"]]
    else:
        my = [
            r for r in reqs
            if r.get("assigned_operator_id") == me["id"] or r.get("assigned_executor_id") == me["id"]
        ]
    if not my:
        await safe_reply(update.message, "У вас пока нет заявок.")
        return
    lines = []
    for r in my[:20]:
        line = f"№{r['id']} — {r['title']} ({request_status_ru(r['status'])})"
        if r.get("photo_file_id"):
            line += " 📷"
        lines.append(line)
    await safe_reply(update.message, "Ваши заявки:\n" + "\n".join(lines))


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await safe_reply(
        update.message,
        "Команды:\n"
        "/start — начать\n"
        "/new — создать заявку (название → адрес → описание → фото)\n"
        "/list — мои заявки\n"
        "/skip — пропустить фото на шаге 4\n"
        "/help — эта справка",
    )
