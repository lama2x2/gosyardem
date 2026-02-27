from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class RequestStatus(str, Enum):
    created = "created"
    in_progress = "in_progress"
    proof_under_review = "proof_under_review"
    completed = "completed"
    rejected = "rejected"


class CitizenRequestCreate(BaseModel):
    """Создание заявки гражданином. user_id — ID пользователя (гражданина)."""

    user_id: int
    title: str
    description: Optional[str] = None
    address: Optional[str] = None
    type_id: Optional[int] = None


class CitizenRequestUpdate(BaseModel):
    """Обновление заявки (статус — исполнитель/оператор; оценка и отзыв — гражданин)."""

    status: Optional[RequestStatus] = None
    rating: Optional[int] = Field(None, ge=1, le=5)
    citizen_confirmed: Optional[bool] = None
    citizen_review: Optional[str] = None
    assigned_operator_id: Optional[int] = None
    assigned_executor_id: Optional[int] = None


class CitizenRequestRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    type_id: Optional[int]
    status: RequestStatus
    assigned_operator_id: Optional[int]
    assigned_executor_id: Optional[int]
    title: str
    description: Optional[str]
    address: Optional[str]
    rating: Optional[int]
    citizen_confirmed: Optional[bool]
    citizen_review: Optional[str]
    created_at: datetime
    updated_at: datetime
