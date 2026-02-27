from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict


class UserRole(str, Enum):
    citizen = "citizen"
    operator = "operator"
    executor = "executor"
    superuser = "superuser"


class UserSource(str, Enum):
    telegram = "telegram"
    api = "api"


class UserBase(BaseModel):
    username: Optional[str] = None
    role: UserRole = UserRole.citizen
    source: UserSource = UserSource.telegram


class UserCreate(BaseModel):
    """Создание пользователя (оператор/исполнитель/суперюзер): логин, пароль, telegram_id. Для гражданина — только telegram_id."""

    username: Optional[str] = None
    password: Optional[str] = None
    telegram_id: Optional[int] = None
    role: UserRole = UserRole.citizen


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    telegram_id: Optional[int]
    username: Optional[str]
    role: UserRole
    source: UserSource
    created_at: datetime
