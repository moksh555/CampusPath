"""Shared route dependencies."""

import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models import Chat
from app.services.chat_service import load_chat

DbSession = Annotated[Session, Depends(get_db)]
CurrentUserId = Annotated[str, Depends(get_current_user_id)]


def require_owned_chat(
    chat_id: uuid.UUID, db: DbSession, user_id: CurrentUserId
) -> Chat:
    """Load a chat or 404. Another user's chat is indistinguishable from a missing one."""
    chat = load_chat(db, chat_id, user_id)
    if chat is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found"
        )
    return chat


OwnedChat = Annotated[Chat, Depends(require_owned_chat)]
