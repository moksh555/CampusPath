"""Adopt existing identity records into the auth-owned schema without changing IDs."""

from alembic import op
from sqlalchemy import inspect, text

from app.authentication import models  # noqa: F401
from app.models import Base

revision = "identity_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    connection = op.get_bind()
    inspector = inspect(connection)
    existing = set(inspector.get_table_names(schema="public"))
    owned = set(inspector.get_table_names(schema="identity"))
    tables = ["users", "login_sessions", "refresh_tokens", "oauth_attempts"]
    for name in tables:
        if name in existing and name in owned:
            raise RuntimeError(
                "Both public and identity tables exist; resolve data ownership before migrating"
            )
        if name in existing:
            connection.execute(text(f"ALTER TABLE public.{name} SET SCHEMA identity"))
    Base.metadata.create_all(connection)


def downgrade():
    raise RuntimeError(
        "Identity migration preserves live sessions; restore a backup to roll back"
    )
