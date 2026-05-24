"""Синхронизация имени из профиля Telegram с бэкендом."""

from __future__ import annotations

from typing import Optional

from telegram import Update
from telegram import User as TgUser

from app.bot import api_client


def display_name_from_telegram(user: Optional[TgUser]) -> Optional[str]:
    if not user:
        return None
    parts = []
    if user.first_name:
        parts.append(user.first_name.strip())
    if user.last_name:
        parts.append(user.last_name.strip())
    name = " ".join(parts).strip()
    if name:
        return name
    if user.username:
        return f"@{user.username}"
    return None


async def sync_profile(update: Update) -> None:
    """Сохранить актуальное имя из Telegram при любом обращении к боту."""
    tg_user = update.effective_user
    name = display_name_from_telegram(tg_user)
    if not tg_user or not name:
        return
    await api_client.sync_telegram_profile(tg_user.id, name)
