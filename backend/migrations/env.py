from alembic import context
from app.core.database import engine
from app.models import Base
from app.modules.auth import models as auth_models
from app.modules.research import models as research_models

with engine.connect() as connection:
    context.configure(connection=connection, target_metadata=Base.metadata)
    with context.begin_transaction():
        context.run_migrations()
