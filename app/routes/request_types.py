"""Типы заявок (заглушка под зоны ответственности)."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import RequestType
from app.schemas.request_type import RequestTypeCreate, RequestTypeRead

router = APIRouter()


@router.get("/", response_model=List[RequestTypeRead])
async def list_request_types(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(RequestType))
    return list(result.scalars().all())


@router.post("/", response_model=RequestTypeRead)
async def create_request_type(body: RequestTypeCreate, db: AsyncSession = Depends(get_db)):
    rt = RequestType(name=body.name, slug=body.slug)
    db.add(rt)
    await db.flush()
    await db.refresh(rt)
    return rt


@router.get("/{type_id}", response_model=RequestTypeRead)
async def get_request_type(type_id: int, db: AsyncSession = Depends(get_db)):
    rt = await db.get(RequestType, type_id)
    if not rt:
        raise HTTPException(404, "Request type not found")
    return rt
