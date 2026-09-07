"""Shared route dependencies."""

import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.integrations.identity import authorize
from app.models import Chat
from app.services.chat_service import load_chat

DbSession = Annotated[Session, Depends(get_db)]
CurrentUserId = Annotated[str, Depends(get_current_user_id)]


def require_owned_chat(
    chat_id: uuid.UUID, request: Request, db: DbSession, user_id: CurrentUserId
) -> Chat:
    """Load a chat or 404. Another user's chat is indistinguishable from a missing one."""
    chat = load_chat(db, chat_id, user_id)
    if chat is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found"
        )
    action = (
        "platform:read"
        if request.method in ("GET", "HEAD", "OPTIONS")
        else "platform:write"
    )
    decision_user = authorize(
        request.cookies.get("access_token", ""), action, chat.user_id
    )
    if decision_user != user_id:
        raise HTTPException(403, "Identity changed during authorization")
    if request.method not in ("GET", "HEAD", "OPTIONS"):
        db.refresh(chat, with_for_update=True)
        db.expire(chat, ["colleges", "columns"])
    return chat


OwnedChat = Annotated[Chat, Depends(require_owned_chat)]
