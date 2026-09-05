"""Request/response shapes for college rows and directory search."""

import uuid

from pydantic import BaseModel, Field

from app.schemas.table import CellOut


class CollegeSearchResult(BaseModel):
    """A hit from the public university directory, not yet saved to a chat."""

    name: str
    country: str | None = Field(default=None, max_length=255)


class CollegeCreate(BaseModel):
    model_config = {"str_strip_whitespace": True}
    name: str = Field(min_length=1, max_length=500)
    country: str | None = Field(default=None, max_length=255)
    major_override: str | None = Field(default=None, max_length=255)


class CollegeUpdate(BaseModel):
    major_override: str | None = Field(default=None, max_length=255)


class CollegeOut(BaseModel):
    id: uuid.UUID
    name: str
    country: str | None
    major_override: str | None
    cells: list[CellOut] = []

    model_config = {"from_attributes": True}
