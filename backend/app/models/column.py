"""A comparison column: the four defaults plus any the user adds."""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.chat import Chat

if TYPE_CHECKING:
    from app.models.cell import Cell


class ColumnDef(Base):
    __tablename__ = "column_defs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    chat_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("chats.id", ondelete="CASCADE")
    )
    key: Mapped[str] = mapped_column(String(255))
    label: Mapped[str] = mapped_column(String(255))
    is_default: Mapped[bool] = mapped_column(default=False)
    sort_order: Mapped[int] = mapped_column(default=0)

    chat: Mapped[Chat] = relationship(back_populates="columns")
    cells: Mapped[list["Cell"]] = relationship(
        back_populates="column", cascade="all, delete-orphan"
    )
