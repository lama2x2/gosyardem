from __future__ import annotations

import enum
from datetime import datetime
from typing import List, Optional

from sqlalchemy import String, Text, DateTime, ForeignKey, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class RequestStatus(str, enum.Enum):
    created = "created"
    in_progress = "in_progress"
    proof_under_review = "proof_under_review"
    completed = "completed"
    rejected = "rejected"


class CitizenRequest(Base):
    __tablename__ = "requests"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    type_id: Mapped[Optional[int]] = mapped_column(ForeignKey("request_types.id"), nullable=True, index=True)
    status: Mapped[RequestStatus] = mapped_column(
        default=RequestStatus.created, nullable=False
    )
    assigned_operator_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id"), nullable=True, index=True
    )
    assigned_executor_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id"), nullable=True, index=True
    )

    title: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    address: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    citizen_confirmed: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    citizen_review: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    citizen: Mapped["User"] = relationship(
        "User", back_populates="requests_created", foreign_keys=[user_id]
    )
    assigned_operator: Mapped[Optional["User"]] = relationship(
        "User", back_populates="requests_operated", foreign_keys=[assigned_operator_id]
    )
    assigned_executor: Mapped[Optional["User"]] = relationship(
        "User", back_populates="requests_executed", foreign_keys=[assigned_executor_id]
    )
    request_type: Mapped[Optional["RequestType"]] = relationship(
        "RequestType", back_populates="requests"
    )
    proofs: Mapped[List["Proof"]] = relationship("Proof", back_populates="request")
