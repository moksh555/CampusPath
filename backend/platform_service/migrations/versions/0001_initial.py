"""Initial platform comparison and research schema.

Supports the previous comparison-only schema without deleting its records.
"""

from alembic import op
from sqlalchemy import inspect, text

from app.models import Base

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    connection = op.get_bind()
    inspector = inspect(connection)
    if "chats" in inspector.get_table_names():
        columns = {c["name"] for c in inspector.get_columns("chats")}
        if "clerk_user_id" in columns:
            op.alter_column("chats", "clerk_user_id", new_column_name="user_id")
        # Previous Clerk ownership is deliberately not mapped by email.
        for sql in [
            "ALTER TABLE cells ADD COLUMN IF NOT EXISTS sources JSON NOT NULL DEFAULT '[]'",
            "ALTER TABLE cells ADD COLUMN IF NOT EXISTS researched_at TIMESTAMPTZ",
            "ALTER TABLE cells ADD COLUMN IF NOT EXISTS revision INTEGER NOT NULL DEFAULT 0",
        ]:
            connection.execute(text(sql))
    # Existing deployments are adopted by revision 0002.
    if "chats" not in inspector.get_table_names(schema="public"):
        Base.metadata.create_all(connection)


def downgrade():
    raise RuntimeError(
        "Initial schema downgrade would destroy data; restore a database backup instead."
    )
