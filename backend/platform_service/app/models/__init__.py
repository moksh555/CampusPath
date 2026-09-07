"""SQLAlchemy tables, one module per table."""

from app.models.base import Base
from app.models.chat import Chat
from app.models.college import CollegeRow
from app.models.column import ColumnDef

__all__ = ["Base", "Chat", "CollegeRow", "ColumnDef"]
