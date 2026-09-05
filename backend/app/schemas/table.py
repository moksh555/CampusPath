"""Request/response shapes for comparison columns and cells."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ColumnCreate(BaseModel):
    model_config = {"str_strip_whitespace": True}
    label: str = Field(min_length=1, max_length=255)


class ColumnOut(BaseModel):
    id: uuid.UUID
    key: str
    label: str
    is_default: bool
    sort_order: int

    model_config = {"from_attributes": True}


class CellOut(BaseModel):
    id: uuid.UUID
    column_id: uuid.UUID
    value: str
    status: str
    sources: list[dict] = Field(default_factory=list)
    researched_at: datetime | None = None

    model_config = {"from_attributes": True}
