from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ProofStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class ProofCreate(BaseModel):
    """Исполнитель прикладывает пруф к заявке. executor_id — ID исполнителя."""

    request_id: int
    executor_id: int
    file_ref: str
    comment: Optional[str] = None


class ProofDecide(BaseModel):
    """Оператор подтверждает или отклоняет пруф."""

    operator_id: int
    status: ProofStatus  # approved | rejected


class ProofRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    request_id: int
    executor_id: int
    operator_id: Optional[int]
    file_ref: str
    comment: Optional[str]
    status: ProofStatus
    created_at: datetime
