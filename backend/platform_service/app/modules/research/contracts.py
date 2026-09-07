"""Version 2 session research contract; IDs, not names, identify table cells."""

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl, model_validator

ErrorCode = Literal[
    "no_content", "invalid_response", "provider_error", "timeout", "agent_error"
]


class Source(BaseModel):
    title: str = ""
    url: HttpUrl


class AgentResult(BaseModel):
    """One subagent's factual answer."""

    model_config = {"str_strip_whitespace": True}
    answer: str = Field(min_length=1, max_length=100000)
    sources: list[Source] = Field(default_factory=list)


class University(BaseModel):
    id: UUID
    name: str
    country: str | None = None
    major: str | None = None


class Question(BaseModel):
    id: UUID
    label: str


class Target(BaseModel):
    row_id: UUID
    column_id: UUID


class SessionPayload(BaseModel):
    session_id: UUID
    revision: int = Field(ge=1)
    major: str | None = None
    universities: list[University] = Field(min_length=1)
    questions: list[Question] = Field(min_length=1)
    targets: list[Target] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_grid(self):
        rows = {row.id for row in self.universities}
        columns = {column.id for column in self.questions}
        pairs = [(target.row_id, target.column_id) for target in self.targets]
        if len(rows) != len(self.universities) or len(columns) != len(self.questions):
            raise ValueError("Duplicate row or column IDs")
        if len(pairs) != len(set(pairs)) or any(
            r not in rows or c not in columns for r, c in pairs
        ):
            raise ValueError("Invalid target grid")
        return self


class CellResearchResult(Target):
    model_config = {"str_strip_whitespace": True}
    status: Literal["completed", "failed"]
    answer: str = Field(default="", max_length=100000)
    sources: list[Source] = Field(default_factory=list)
    error_code: ErrorCode | None = None

    @model_validator(mode="after")
    def validate_content(self):
        if self.status == "completed" and (not self.answer or self.error_code):
            raise ValueError("Completed cells require content and no error")
        if self.status == "failed" and (
            self.answer or self.sources or not self.error_code
        ):
            raise ValueError(
                "Failed cells require an error code, not an invented answer"
            )
        return self


class SessionResult(BaseModel):
    cells: list[CellResearchResult] = Field(min_length=1)

    def validate_for(self, payload: SessionPayload):
        expected = {(target.row_id, target.column_id) for target in payload.targets}
        actual = [(cell.row_id, cell.column_id) for cell in self.cells]
        if len(actual) != len(set(actual)) or set(actual) != expected:
            raise ValueError("Results must match every requested cell exactly once")
        return self


class ClaimedJob(BaseModel):
    id: UUID
    attempt: int = Field(ge=1, le=3)
    revision: int = Field(ge=1)
    payload: SessionPayload


class ClaimRequest(BaseModel):
    timeout_seconds: int = Field(ge=1, le=3600)


class Completion(BaseModel):
    attempt: int = Field(ge=1, le=3)
    revision: int = Field(ge=1)
    result: SessionResult | None = None
    error_code: ErrorCode | None = None
