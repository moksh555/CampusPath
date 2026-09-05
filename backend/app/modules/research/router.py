"""Queue research for an owned comparison; repeated clicks do not duplicate work."""

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.api.deps import DbSession, OwnedChat
from app.configuration.settings import settings
from app.models import Cell
from app.modules.research.models import ResearchJob

router = APIRouter(prefix="/chats/{chat_id}/research", tags=["research"])


@router.post("", status_code=202)
def start(chat: OwnedChat, db: DbSession):
    if not settings.agent_entrypoint:
        raise HTTPException(503, "Research is not connected yet. Configure AGENT_ENTRYPOINT.")
    if not chat.colleges or not chat.columns:
        raise HTTPException(422, "Add at least one university and one question")
    columns = {column.id: column.label for column in chat.columns}
    queued = 0
    for college in chat.colleges:
        for existing in college.cells:
            cell = db.scalar(
                select(Cell)
                .where(Cell.id == existing.id)
                .with_for_update()
                .execution_options(populate_existing=True)
            )
            if cell.status in ("queued", "running", "completed"):
                continue
            cell.revision += 1
            cell.status = "queued"
            db.add(
                ResearchJob(
                    cell_id=cell.id,
                    revision=cell.revision,
                    payload={
                        "university": college.name,
                        "country": college.country,
                        "major": college.major_override or chat.major,
                        "question": columns[cell.column_id],
                    },
                )
            )
            queued += 1
    db.commit()
    return {"queued": queued}
