"""One college x column intersection in the comparison table."""

import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.college import CollegeRow
from app.models.column import ColumnDef

# Cells are created empty; the research worker records results and citations.
CELL_STATUSES = ("empty", "queued", "running", "completed", "failed", "stale")


class Cell(Base):
    __tablename__ = "cells"
    __table_args__ = (
        UniqueConstraint("college_row_id", "column_id", name="uq_cell_college_column"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    college_row_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("college_rows.id", ondelete="CASCADE")
    )
    column_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("column_defs.id", ondelete="CASCADE")
    )
    value: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(32), default="empty")

    sources: Mapped[list] = mapped_column(JSON, default=list)
    researched_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    revision: Mapped[int] = mapped_column(default=0)

    college: Mapped[CollegeRow] = relationship(back_populates="cells")
    column: Mapped[ColumnDef] = relationship(back_populates="cells")
