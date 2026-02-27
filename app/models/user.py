from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import String, BigInteger, Enum, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base

if TYPE_CHECKING:
    from app.models.request import CitizenRequest
    from app.models.proof import Proof


class UserSource(str, enum.Enum):
    telegram = "telegram"
    api = "api"


class UserRole(str, enum.Enum):
    citizen = "citizen"
    operator = "operator"
    executor = "executor"
    superuser = "superuser"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    telegram_id: Mapped[Optional[int]] = mapped_column(BigInteger, unique=True, nullable=True, index=True)
    username: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True, index=True)
    password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.citizen, nullable=False)
    source: Mapped[UserSource] = mapped_column(Enum(UserSource), default=UserSource.telegram, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    requests_created: Mapped[List["CitizenRequest"]] = relationship(
        "CitizenRequest", back_populates="citizen", foreign_keys="CitizenRequest.user_id"
    )
    requests_operated: Mapped[List["CitizenRequest"]] = relationship(
        "CitizenRequest", back_populates="assigned_operator", foreign_keys="CitizenRequest.assigned_operator_id"
    )
    requests_executed: Mapped[List["CitizenRequest"]] = relationship(
        "CitizenRequest", back_populates="assigned_executor", foreign_keys="CitizenRequest.assigned_executor_id"
    )
    proofs: Mapped[List["Proof"]] = relationship("Proof", back_populates="executor", foreign_keys="Proof.executor_id")
    proofs_decided: Mapped[List["Proof"]] = relationship(
        "Proof", back_populates="operator", foreign_keys="Proof.operator_id"
    )
