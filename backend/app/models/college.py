"""One college row in a chat's comparison table."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.chat import Chat

if TYPE_CHECKING:
    from app.models.cell import Cell


class CollegeRow(Base):
    __tablename__ = "college_rows"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    chat_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("chats.id", ondelete="CASCADE")
    )
    name: Mapped[str] = mapped_column(String(500))
    country: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Falls back to the chat-level major when null.
    major_override: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    chat: Mapped[Chat] = relationship(back_populates="colleges")
    cells: Mapped[list["Cell"]] = relationship(
        back_populates="college", cascade="all, delete-orphan"
    )
