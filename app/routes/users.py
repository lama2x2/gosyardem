"""Пользователи: список, создание операторов/исполнителей/суперюзера (по роли)."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import User
from app.models.user import UserRole
from app.schemas.user import UserCreate, UserRead
from app.auth import get_password_hash

router = APIRouter()


@router.get("/", response_model=List[UserRead])
async def list_users(db: AsyncSession = Depends(get_db)):
    """Список пользователей (для админки/операций)."""
    result = await db.execute(select(User))
    return list(result.scalars().all())


@router.get("/by-telegram/{telegram_id}", response_model=UserRead)
async def get_user_by_telegram(telegram_id: int, db: AsyncSession = Depends(get_db)):
    """Найти пользователя по Telegram ID (для бота)."""
    result = await db.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User not found")
    return user


@router.get("/{user_id}", response_model=UserRead)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(404, "User not found")
    return user


@router.post("/", response_model=UserRead)
async def create_user(body: UserCreate, db: AsyncSession = Depends(get_db)):
    """
    Создание пользователя. Для гражданина — только telegram_id (username опционально tg_{id}).
    Для operator/executor/superuser — username, password, telegram_id.
    """
    if body.role == UserRole.citizen:
        if body.telegram_id is None:
            raise HTTPException(400, "Citizen requires telegram_id")
        result = await db.execute(select(User).where(User.telegram_id == body.telegram_id))
        if result.scalar_one_or_none():
            raise HTTPException(400, "User with this telegram_id already exists")
        username = body.username or f"tg_{body.telegram_id}"
        user = User(
            username=username,
            password_hash=None,
            role=UserRole.citizen,
            telegram_id=body.telegram_id,
        )
    else:
        if not body.username or not body.password:
            raise HTTPException(400, "Operator/executor/superuser require username and password")
        existing = await db.execute(select(User).where(User.username == body.username))
        if existing.scalar_one_or_none():
            raise HTTPException(400, "Username already exists")
        user = User(
            username=body.username,
            password_hash=get_password_hash(body.password),
            role=UserRole(body.role.value),
            telegram_id=body.telegram_id,
        )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user
