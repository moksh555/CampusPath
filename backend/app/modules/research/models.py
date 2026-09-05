"""Durable per-cell jobs with leases and revision protection."""

import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ResearchJob(Base):
    __tablename__ = "research_jobs"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    cell_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cells.id", ondelete="CASCADE"), index=True
    )
    revision: Mapped[int]
    payload: Mapped[dict] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(default="queued", index=True)
    attempts: Mapped[int] = mapped_column(default=0)
    lease_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
