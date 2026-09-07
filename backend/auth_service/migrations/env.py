from alembic import context
from sqlalchemy import text

from app.authentication import models  # noqa: F401
from app.core.database import engine
from app.models import Base

with engine.begin() as connection:
    connection.execute(text("CREATE SCHEMA IF NOT EXISTS identity"))
with engine.connect() as connection:
    context.configure(
        connection=connection,
        target_metadata=Base.metadata,
        version_table_schema="identity",
        include_schemas=True,
    )
    with context.begin_transaction():
        context.run_migrations()
