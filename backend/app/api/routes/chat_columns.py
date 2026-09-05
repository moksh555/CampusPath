"""/chats/{chat_id}/columns — user-defined comparison columns."""

import uuid

from fastapi import APIRouter, HTTPException, status

from app.api.deps import DbSession, OwnedChat
from app.schemas.table import ColumnCreate, ColumnOut
from app.services.table_service import add_column

router = APIRouter(prefix="/chats/{chat_id}/columns", tags=["columns"])


@router.post("", response_model=ColumnOut, status_code=status.HTTP_201_CREATED)
def create_column(body: ColumnCreate, chat: OwnedChat, db: DbSession):
    column = add_column(db, chat, body.label.strip())
    db.commit()
    db.refresh(column)
    return column


@router.delete("/{column_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_column(column_id: uuid.UUID, chat: OwnedChat, db: DbSession) -> None:
    column = next((c for c in chat.columns if c.id == column_id), None)
    if column is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Column not found"
        )
    if column.is_default:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Default columns cannot be removed",
        )
    db.delete(column)
    db.commit()
