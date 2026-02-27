"""Заявки: создание, список, обновление статуса, назначение, оценка/отзыв гражданина."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import CitizenRequest, User
from app.models.request import RequestStatus as ModelRequestStatus
from app.schemas.request import (
    CitizenRequestCreate,
    CitizenRequestRead,
    CitizenRequestUpdate,
    RequestStatus,
)

router = APIRouter()


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
        raise HTTPException(404, "User not found")
    req = CitizenRequest(
        user_id=body.user_id,
        type_id=body.type_id,
        title=body.title,
        description=body.description,
        address=body.address,
        status=ModelRequestStatus.created,
    )
    db.add(req)
    await db.flush()
    await db.refresh(req)
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
