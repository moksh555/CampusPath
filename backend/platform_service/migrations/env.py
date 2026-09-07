from alembic import context
from sqlalchemy import inspect, text

from app.core.database import engine
from app.models import Base
from app.modules.research import models  # noqa: F401

with engine.begin() as connection:
    connection.execute(text("CREATE SCHEMA IF NOT EXISTS platform"))
    inspector = inspect(connection)
    if "alembic_version" in inspector.get_table_names(
        schema="public"
    ) and "alembic_version" not in inspector.get_table_names(schema="platform"):
        connection.execute(
            text("ALTER TABLE public.alembic_version SET SCHEMA platform")
        )
with engine.connect() as connection:
    context.configure(
        connection=connection,
        target_metadata=Base.metadata,
        version_table_schema="platform",
        include_schemas=True,
    )
    with context.begin_transaction():
        context.run_migrations()
