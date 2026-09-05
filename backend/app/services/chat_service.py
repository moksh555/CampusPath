"""Chat lifecycle: create with defaults, load scoped to the owner, update."""

import uuid

from sqlalchemy.orm import Session, selectinload

from app.models import Chat, CollegeRow
from app.schemas.college import CollegeCreate
from app.services.defaults import build_chat_title
from app.services.table_service import add_college


def load_chat(db: Session, chat_id: uuid.UUID, user_id: str) -> Chat | None:
    """Load a chat with its full table, but only if this user owns it."""
    return (
        db.query(Chat)
        .options(
            selectinload(Chat.colleges).selectinload(CollegeRow.cells),
            selectinload(Chat.columns),
        )
        .filter(Chat.id == chat_id, Chat.user_id == user_id)
        .one_or_none()
    )


def list_chats(db: Session, user_id: str) -> list[Chat]:
    return (
        db.query(Chat)
        .filter(Chat.user_id == user_id)
        .order_by(Chat.created_at.desc())
        .all()
    )


def create_chat(
    db: Session,
    user_id: str,
    *,
    title: str | None,
    major: str | None,
    colleges: list[CollegeCreate],
    columns: list[str],
) -> Chat:
    chat = Chat(
        user_id=user_id,
        title=((title or "").strip() or build_chat_title(major, colleges))[:255],
        major=major,
    )
    db.add(chat)
    db.flush()

    from fastapi import HTTPException

    from app.services.table_service import add_column

    for label in columns:
        if not label.strip() or len(label.strip()) > 255:
            raise HTTPException(422, "Column questions must contain 1–255 characters")
        add_column(db, chat, label.strip())
        db.expire(chat, ["columns"])
    for item in colleges:
        add_college(
            db,
            chat,
            name=item.name,
            country=item.country,
            major_override=item.major_override,
        )

    db.commit()
    return chat
