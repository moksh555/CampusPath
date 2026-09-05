"""A chat is one comparison session, owned by a single user."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.college import CollegeRow
    from app.models.column import ColumnDef


class Chat(Base):
    __tablename__ = "chats"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[str] = mapped_column(String(255), index=True)
    title: Mapped[str] = mapped_column(String(255))
    major: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    colleges: Mapped[list["CollegeRow"]] = relationship(
        back_populates="chat",
        cascade="all, delete-orphan",
        order_by="CollegeRow.created_at",
    )
    columns: Mapped[list["ColumnDef"]] = relationship(
        back_populates="chat",
        cascade="all, delete-orphan",
        order_by="ColumnDef.sort_order",
    )
