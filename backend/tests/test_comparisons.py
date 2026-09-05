"""Comparison validation and queue semantics without network or database calls."""

import uuid
from types import SimpleNamespace as NS
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.configuration.settings import settings
from app.modules.research.router import start
from app.schemas.chat import ChatCreate
from app.schemas.college import CollegeCreate, CollegeUpdate
from app.schemas.table import ColumnCreate
from app.services.table_service import (
    add_column,
    add_empty_cells_for_college,
    add_empty_cells_for_column,
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


def test_cells_for_each_dimension():
    db = MagicMock()
    row = NS(id=uuid.uuid4())
    column = NS(id=uuid.uuid4())
    add_empty_cells_for_college(db, row, [column])
    cells = list(db.add_all.call_args.args[0])
    assert len(cells) == 1 and cells[0].column_id == column.id
    add_empty_cells_for_column(db, column, [row])
    cells = list(db.add_all.call_args.args[0])
    assert len(cells) == 1 and cells[0].college_row_id == row.id


def test_column_order_after_deletion():
    db = MagicMock()
    chat = NS(id=uuid.uuid4(), columns=[NS(sort_order=4, key="fees")], colleges=[])
    column = add_column(db, chat, "Fees")
    assert column.sort_order == 5 and column.key == "fees-2"


def test_research_requires_configuration(monkeypatch):
    monkeypatch.setattr(settings, "agent_entrypoint", "")
    with pytest.raises(HTTPException) as error:
        start(NS(), MagicMock())
    assert error.value.status_code == 503


@pytest.mark.parametrize(
    "status,expected",
    [
        ("empty", 1),
        ("failed", 1),
        ("stale", 1),
        ("running", 0),
        ("queued", 0),
        ("completed", 0),
    ],
)
def test_queue_idempotence(monkeypatch, status, expected):
    monkeypatch.setattr(settings, "agent_entrypoint", "research:research")
    column = NS(id=uuid.uuid4(), label="Annual fees")
    cell = NS(id=uuid.uuid4(), column_id=column.id, status=status, revision=0)
    row = NS(name="University", country="US", major_override="CS", cells=[cell])
    chat = NS(colleges=[row], columns=[column], major="Math")
    db = MagicMock()
    db.scalar.return_value = cell
    assert start(chat, db) == {"queued": expected}
    if expected:
        assert db.add.call_args.args[0].payload["major"] == "CS"
        assert cell.status == "queued" and cell.revision == 1
