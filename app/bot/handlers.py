"""
Обработчики Telegram-бота.
Вся логика работы — в телеге; бот дергает API бэкенда (FastAPI).
При первом запуске бота оператор/исполнитель/суперюзер привязывается по telegram_id.
"""

from typing import Optional

import httpx
from telegram import Update
from telegram.ext import ContextTypes

from app.config import settings

API_BASE = f"{settings.api_base_url.rstrip('/')}/api"


async def get_user_by_telegram_id(telegram_id: int) -> Optional[dict]:
    """Найти пользователя по telegram_id через API."""
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{API_BASE}/users/by-telegram/{telegram_id}")
        if r.status_code != 200:
            return None
        return r.json()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /start — приветствие; регистрация гражданина по telegram_id если ещё нет."""
    user = update.effective_user
    if not user or not update.message:
        return
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{API_BASE}/users/by-telegram/{user.id}")
        if r.status_code == 404:
            reg = await client.post(
                f"{API_BASE}/users/",
                json={"telegram_id": user.id, "role": "citizen"},
            )
            if reg.status_code in (200, 201):
                await update.message.reply_text(
                    "Добро пожаловать! Вы зарегистрированы как гражданин. "
                    "Используйте /new для создания заявки, /list — для просмотра заявок."
                )
                return
        elif r.status_code == 200:
            await update.message.reply_text(
                "С возвращением! Используйте /new для заявки, /list — мои заявки, /help — справка."
            )
            return
    await update.message.reply_text(
        "Платформа помощи гражданам. Используйте /help для списка команд."
    )


async def create_request_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Начало создания заявки — запрос названия."""
    await update.message.reply_text("Введите краткое название проблемы (например: «Яма на дороге»):")
    context.user_data["creating_request"] = {"step": "title"}


async def create_request_title(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Получение названия заявки."""
    if context.user_data.get("creating_request", {}).get("step") != "title":
        return
    context.user_data["creating_request"]["title"] = update.message.text
    context.user_data["creating_request"]["step"] = "description"
    await update.message.reply_text("Опишите проблему подробнее (адрес, что именно не так):")


async def handle_create_request_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Маршрутизация текста при создании заявки по шагу."""
    step = context.user_data.get("creating_request", {}).get("step")
    if step == "title":
        await create_request_title(update, context)
    elif step == "description":
        await create_request_description(update, context)


async def create_request_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Получение описания и отправка заявки в API."""
    data = context.user_data.get("creating_request")
    if not data or data.get("step") != "description":
        return
    title = data.get("title", "")
    description = update.message.text or ""
    telegram_id = update.effective_user.id if update.effective_user else 0

    citizen = await get_user_by_telegram_id(telegram_id)
    if not citizen:
        await update.message.reply_text(
            "Вы не зарегистрированы. Нажмите /start для регистрации."
        )
        context.user_data.pop("creating_request", None)
        return
    user_id = citizen["id"]

    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"{API_BASE}/requests/",
            json={
                "user_id": user_id,
                "title": title,
                "description": description,
                "address": None,
                "type_id": None,
            },
        )
    context.user_data.pop("creating_request", None)
    if r.status_code in (200, 201):
        req = r.json()
        await update.message.reply_text(
            f"Заявка №{req['id']} создана. Статус: {req['status']}. Вы получите уведомление при изменении."
        )
    else:
        await update.message.reply_text("Не удалось создать заявку. Попробуйте позже.")


async def my_requests(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Список заявок пользователя (гражданин — свои, оператор/исполнитель — назначенные)."""
    telegram_id = update.effective_user.id if update.effective_user else 0
    me = await get_user_by_telegram_id(telegram_id)
    if not me:
        await update.message.reply_text("Пользователь не найден. Нажмите /start.")
        return
    async with httpx.AsyncClient() as client:
        reqs_r = await client.get(f"{API_BASE}/requests/")
        if reqs_r.status_code != 200:
            await update.message.reply_text("Ошибка загрузки заявок.")
            return
        reqs = reqs_r.json()
    if me["role"] == "citizen":
        my = [r for r in reqs if r["user_id"] == me["id"]]
    else:
        my = [
            r for r in reqs
            if r.get("assigned_operator_id") == me["id"] or r.get("assigned_executor_id") == me["id"]
        ]
    if not my:
        await update.message.reply_text("У вас пока нет заявок.")
        return
    lines = [f"№{r['id']} — {r['title']} ({r['status']})" for r in my[:20]]
    await update.message.reply_text("Ваши заявки:\n" + "\n".join(lines))


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Команды:\n"
        "/start — начать\n"
        "/new — создать заявку\n"
        "/list — мои заявки\n"
        "/help — эта справка"
    )
