"""Session job semantics, without external providers."""

import uuid
from types import SimpleNamespace as NS
from unittest.mock import MagicMock

import pytest

from app.modules.research.contracts import (
    CellResearchResult,
    Completion,
    SessionPayload,
    SessionResult,
)
from app.services.research_queue import complete, enqueue
from app.services.session_results import invalidate


def fixture():
    row, column = (
        NS(id=uuid.uuid4(), name="Example", country="Canada", major_override=None),
        NS(id=uuid.uuid4(), label="Fees"),
    )
    chat = NS(
        id=uuid.uuid4(),
        major="CS",
        colleges=[row],
        columns=[column],
        research_results={},
        research_revision=0,
    )
    return chat, row, column


def test_one_session_job_and_result_document():
    chat, row, column = fixture()
    chat.columns.append(NS(id=uuid.uuid4(), label="Courses"))
    db = MagicMock()
    db.scalar.return_value = None
    assert enqueue(db, chat) == {"queued": 1, "cells": 2}
    db.add.assert_called_once()
    job = db.add.call_args.args[0]
    assert job.chat_id == chat.id and len(job.payload["targets"]) == 2
    assert len(chat.research_results[str(row.id)]) == 2


def test_repeat_enqueue_reuses_active_job():
    chat, _, _ = fixture()
    chat.research_revision = 1
    db = MagicMock()
    db.scalar.return_value = NS(revision=1, status="running")
    assert enqueue(db, chat)["queued"] == 0
    db.add.assert_not_called()


@pytest.mark.parametrize("attempt,expected", [(1, "queued"), (3, "failed")])
def test_empty_content_retries_and_records_error(attempt, expected):
    chat, row, column = fixture()
    db = MagicMock()
    db.scalar.return_value = None
    enqueue(db, chat)
    job = db.add.call_args.args[0]
    job.id = uuid.uuid4()
    job.attempts = attempt
    job.status = "running"
    db.scalar.side_effect = [job, chat, job]
    payload = SessionPayload.model_validate(job.payload)
    result = SessionResult(
        cells=[
            CellResearchResult(
                **payload.targets[0].model_dump(),
                status="failed",
                error_code="no_content",
            )
        ]
    )
    assert complete(
        db, job.id, Completion(attempt=attempt, revision=job.revision, result=result)
    )
    cell = chat.research_results[str(row.id)][str(column.id)]
    assert job.status == cell["status"] == expected
    assert cell["error_code"] == "no_content" and "no content" in cell["error_message"]


def test_old_completion_cannot_overwrite_edit():
    chat, row, column = fixture()
    db = MagicMock()
    db.scalar.return_value = None
    enqueue(db, chat)
    job = db.add.call_args.args[0]
    job.id = uuid.uuid4()
    job.attempts = 1
    job.status = "running"
    invalidate(chat)
    db.scalar.side_effect = [job, chat, job]
    assert not complete(
        db,
        job.id,
        Completion(attempt=1, revision=job.revision, error_code="no_content"),
    )
    assert job.status == "superseded"
