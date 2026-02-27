from __future__ import annotations

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import String, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class ProofStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class Proof(Base):
    __tablename__ = "proofs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    request_id: Mapped[int] = mapped_column(ForeignKey("requests.id"), nullable=False, index=True)
    executor_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    operator_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)

    file_ref: Mapped[str] = mapped_column(String(512), nullable=False)
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[ProofStatus] = mapped_column(default=ProofStatus.pending, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    request: Mapped["CitizenRequest"] = relationship("CitizenRequest", back_populates="proofs")
    executor: Mapped["User"] = relationship("User", back_populates="proofs", foreign_keys=[executor_id])
    operator: Mapped[Optional["User"]] = relationship(
        "User", back_populates="proofs_decided", foreign_keys=[operator_id]
    )
