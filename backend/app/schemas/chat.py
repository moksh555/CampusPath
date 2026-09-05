"""Request/response shapes for comparison chats."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.college import CollegeCreate, CollegeOut
from app.schemas.table import ColumnOut


class ChatCreate(BaseModel):
    title: str | None = Field(default=None, max_length=255)
    major: str | None = Field(default=None, max_length=255)
    colleges: list[CollegeCreate] = Field(default_factory=list)
    columns: list[str] = Field(default_factory=list)


class ChatUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=255)
    major: str | None = Field(default=None, max_length=255)


class ChatSummary(BaseModel):
    id: uuid.UUID
    title: str
    major: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatDetail(ChatSummary):
    colleges: list[CollegeOut]
    columns: list[ColumnOut]
