"""Account persistence keyed by Google's stable subject identifier."""

import uuid

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.modules.auth.models import User


def upsert_google_user(db: Session, claims: dict) -> User:
    """Concurrent callbacks for the same identity must create only one user."""
    profile = {"email": claims["email"], "name": claims.get("name", "Student")}
    statement = (
        insert(User)
        .values(id=str(uuid.uuid4()), google_subject=claims["sub"], **profile)
        .on_conflict_do_update(index_elements=[User.google_subject], set_=profile)
        .returning(User)
    )
    return db.scalar(statement)
