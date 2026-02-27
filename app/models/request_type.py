from __future__ import annotations

from typing import List

from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class RequestType(Base):
    """Заглушка для зон ответственности на будущее."""

    __tablename__ = "request_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)

    requests: Mapped[List["CitizenRequest"]] = relationship(
        "CitizenRequest", back_populates="request_type"
    )
