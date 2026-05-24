"""Заявки: создание, список, обновление статуса, назначение, оценка/отзыв гражданина."""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import CitizenRequest, User
from app.models.request import RequestStatus as ModelRequestStatus
from app.models.user import UserRole
from app.schemas.request import (
    CitizenRequestCreate,
    CitizenRequestRead,
    CitizenRequestUpdate,
    RequestStatus,
)

router = APIRouter()
logger = logging.getLogger(__name__)


async def _operator_ids(db: AsyncSession) -> list[int]:
    result = await db.execute(select(User.id).where(User.role == UserRole.operator))
    return [row[0] for row in result.all()]


def _pick_assigned_operator(operator_ids: list[int]) -> Optional[int]:
    if len(operator_ids) == 1:
        return operator_ids[0]
    return None


@router.get("/", response_model=List[CitizenRequestRead])
async def list_requests(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(CitizenRequest).order_by(CitizenRequest.created_at.desc())
    )
    return list(result.scalars().all())


@router.post("/", response_model=CitizenRequestRead)
async def create_request(
    body: CitizenRequestCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Создание заявки. user_id в теле запроса (в MVP из бота — по telegram_id находят user_id).
    """
    user = await db.get(User, body.user_id)
    if not user:
        logger.warning("Создание заявки отклонено: пользователь user_id=%s не найден", body.user_id)
        raise HTTPException(404, "User not found")

    operator_ids = await _operator_ids(db)
    assigned_operator_id = _pick_assigned_operator(operator_ids)

    logger.info(
        "Заявка: входящие данные — user_id=%s role=%s telegram_id=%s username=%s "
        "title=%r address=%r type_id=%s has_photo=%s operators_in_db=%s",
        user.id,
        user.role.value,
        user.telegram_id,
        user.username,
        body.title,
        body.address,
        body.type_id,
        bool(body.photo_file_id),
        operator_ids,
    )

    if assigned_operator_id is not None:
        logger.info("Заявка: автоназначение на operator_id=%s", assigned_operator_id)
    else:
        logger.info(
            "Заявка: автоназначение не выполнено (операторов=%s, нужен ровно 1)",
            len(operator_ids),
        )

    req = CitizenRequest(
        user_id=body.user_id,
        type_id=body.type_id,
        title=body.title,
        description=body.description,
        address=body.address,
        photo_file_id=body.photo_file_id,
        assigned_operator_id=assigned_operator_id,
        status=ModelRequestStatus.created,
    )
    db.add(req)
    await db.flush()
    await db.refresh(req)

    logger.info(
        "Заявка создана: id=%s user_id=%s status=%s operator_id=%s executor_id=%s "
        "title=%r address=%r photo_file_id=%s",
        req.id,
        req.user_id,
        req.status.value,
        req.assigned_operator_id,
        req.assigned_executor_id,
        req.title,
        req.address,
        req.photo_file_id or "—",
    )
    return req


@router.get("/{request_id}", response_model=CitizenRequestRead)
async def get_request(request_id: int, db: AsyncSession = Depends(get_db)):
    req = await db.get(CitizenRequest, request_id)
    if not req:
        raise HTTPException(404, "Request not found")
    return req


@router.patch("/{request_id}", response_model=CitizenRequestRead)
async def update_request(
    request_id: int,
    body: CitizenRequestUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Обновление заявки: статус, назначение оператора/исполнителя, оценка, отзыв."""
    req = await db.get(CitizenRequest, request_id)
    if not req:
        raise HTTPException(404, "Request not found")
    if body.status is not None:
        req.status = ModelRequestStatus(body.status.value)
    if body.rating is not None:
        req.rating = body.rating
    if body.citizen_confirmed is not None:
        req.citizen_confirmed = body.citizen_confirmed
    if body.citizen_review is not None:
        req.citizen_review = body.citizen_review
    if body.assigned_operator_id is not None:
        req.assigned_operator_id = body.assigned_operator_id
    if body.assigned_executor_id is not None:
        req.assigned_executor_id = body.assigned_executor_id
    await db.flush()
    await db.refresh(req)
    return req
