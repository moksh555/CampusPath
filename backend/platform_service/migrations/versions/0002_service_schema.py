"""Move platform-owned tables into a schema with its own migration history."""

from alembic import op
from sqlalchemy import inspect, text

from app.models import Base
from app.modules.research import models  # noqa: F401

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade():
    connection = op.get_bind()
    inspector = inspect(connection)
    existing = set(inspector.get_table_names(schema="public"))
    owned = set(inspector.get_table_names(schema="platform"))
    for name in ["chats", "college_rows", "column_defs", "cells", "research_jobs"]:
        if name in existing and name in owned:
            raise RuntimeError(
                "Both public and platform tables exist; resolve data ownership before migrating"
            )
        if name in existing:
            connection.execute(text(f"ALTER TABLE public.{name} SET SCHEMA platform"))
    Base.metadata.create_all(connection)


def downgrade():
    raise RuntimeError("Service schema migration must be rolled back from a backup")
