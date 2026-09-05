"""/chats — create, list, read, rename, set the chat-wide major, delete."""

import uuid

from fastapi import APIRouter, status

from app.api.deps import CurrentUserId, DbSession, OwnedChat
from app.schemas.chat import ChatCreate, ChatDetail, ChatSummary, ChatUpdate
from app.services import chat_service

router = APIRouter(prefix="/chats", tags=["chats"])


@router.get("", response_model=list[ChatSummary])
def list_chats(db: DbSession, user_id: CurrentUserId):
    return chat_service.list_chats(db, user_id)


@router.post("", response_model=ChatDetail, status_code=status.HTTP_201_CREATED)
def create_chat(body: ChatCreate, db: DbSession, user_id: CurrentUserId):
    major = (body.major or "").strip() or None
    colleges = [c for c in body.colleges if c.name.strip()]
    chat = chat_service.create_chat(
        db,
        user_id,
        title=body.title,
        major=major,
        colleges=colleges,
        columns=body.columns,
    )
    return chat_service.load_chat(db, chat.id, user_id)


@router.get("/{chat_id}", response_model=ChatDetail)
def get_chat(chat: OwnedChat):
    return chat


@router.patch("/{chat_id}", response_model=ChatDetail)
def update_chat(
    chat_id: uuid.UUID,
    body: ChatUpdate,
    chat: OwnedChat,
    db: DbSession,
    user_id: CurrentUserId,
):
    if body.title is not None and body.title.strip():
        chat.title = body.title.strip()
    major = (body.major or "").strip() or None
    if "major" in body.model_fields_set and major != chat.major:
        chat.major = major
        for row in chat.colleges:
            for cell in row.cells:
                cell.revision += 1
                cell.status = "stale"
    db.commit()
    return chat_service.load_chat(db, chat_id, user_id)


@router.delete("/{chat_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_chat(chat: OwnedChat, db: DbSession) -> None:
    db.delete(chat)
    db.commit()
