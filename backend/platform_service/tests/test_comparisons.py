"""Comparison validation and queue semantics without network or database calls."""

import uuid
from types import SimpleNamespace as NS
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from pydantic import SecretStr, ValidationError

from app.configuration.settings import settings
from app.modules.research.router import start
from app.schemas.chat import ChatCreate
from app.schemas.college import CollegeCreate, CollegeUpdate
from app.schemas.table import ColumnCreate
from app.services.table_service import (
    add_column,
)


@pytest.mark.parametrize(
    "model,payload",
    [
        (CollegeCreate, {"name": " "}),
        (CollegeCreate, {"name": "x" * 501}),
        (ColumnCreate, {"label": " "}),
        (ColumnCreate, {"label": "x" * 256}),
        (CollegeUpdate, {"major_override": "x" * 256}),
        (ChatCreate, {"title": "x" * 256}),
    ],
)
def test_validation_edges(model, payload):
    with pytest.raises(ValidationError):
        model(**payload)


def test_draft_and_independent_lists():
    first, second = ChatCreate(), ChatCreate()
    first.columns.append("Fees")
    assert second.columns == [] and second.colleges == []


def test_whitespace_trimmed():
    assert CollegeCreate(name="  Example  ").name == "Example"
    assert ColumnCreate(label=" Fees ").label == "Fees"


def test_column_order_after_deletion():
    db = MagicMock()
    chat = NS(
        id=uuid.uuid4(),
        columns=[NS(sort_order=4, key="fees")],
        colleges=[],
        research_revision=0,
        research_results={},
    )
    column = add_column(db, chat, "Fees")
    assert column.sort_order == 5 and column.key == "fees-2"


def test_research_requires_configuration(monkeypatch):
    monkeypatch.setattr(settings, "research_service_token", SecretStr(""))
    with pytest.raises(HTTPException) as error:
        start(NS(), MagicMock())
    assert error.value.status_code == 503
