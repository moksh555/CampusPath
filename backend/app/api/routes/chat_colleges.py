"""/chats/{chat_id}/colleges — the rows of one comparison table."""

import uuid

from fastapi import APIRouter, HTTPException, status

from app.api.deps import DbSession, OwnedChat
from app.models import CollegeRow
from app.schemas.college import CollegeCreate, CollegeOut, CollegeUpdate
from app.services.table_service import add_college

router = APIRouter(prefix="/chats/{chat_id}/colleges", tags=["colleges"])


def _row(chat, row_id: uuid.UUID) -> CollegeRow:
    row = next((c for c in chat.colleges if c.id == row_id), None)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="College not found"
        )
    return row


@router.post("", response_model=CollegeOut, status_code=status.HTTP_201_CREATED)
def create_college(body: CollegeCreate, chat: OwnedChat, db: DbSession):
    college = add_college(
        db,
        chat,
        name=body.name,
        country=body.country,
        major_override=body.major_override,
    )
    db.commit()
    db.refresh(college)
    return college


@router.patch("/{row_id}", response_model=CollegeOut)
def update_college(
    row_id: uuid.UUID, body: CollegeUpdate, chat: OwnedChat, db: DbSession
):
    row = _row(chat, row_id)
    major = (body.major_override or "").strip() or None
    if "major_override" in body.model_fields_set and major != row.major_override:
        row.major_override = major
        for cell in row.cells:
            cell.revision += 1
            cell.status = "stale"
    db.commit()
    db.refresh(row)
    return row


@router.delete("/{row_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_college(row_id: uuid.UUID, chat: OwnedChat, db: DbSession) -> None:
    db.delete(_row(chat, row_id))
    db.commit()
