"""Queue the entire comparison as one durable session job."""

from fastapi import APIRouter, HTTPException

from app.api.deps import DbSession, OwnedChat
from app.configuration.settings import settings
from app.services.research_queue import enqueue

router = APIRouter(prefix="/chats/{chat_id}/research", tags=["research"])


@router.post("", status_code=202)
def start(chat: OwnedChat, db: DbSession):
    if len(settings.research_service_token.get_secret_value()) < 32:
        raise HTTPException(
            503, "Research is not connected yet. Configure RESEARCH_SERVICE_TOKEN."
        )
    if not chat.colleges or not chat.columns:
        raise HTTPException(422, "Add at least one university and one question")
    return enqueue(db, chat)
