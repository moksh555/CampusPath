from types import SimpleNamespace as NS
from unittest.mock import MagicMock, patch

import pytest

from app.integrations.agent.client import AgentResult
from app.workers.research import run_once


def session(value):
    manager = MagicMock()
    manager.__enter__.return_value = value
    return manager


def test_no_job():
    db = MagicMock()
    db.scalar.return_value = None
    with patch("app.workers.research.SessionLocal", return_value=session(db)):
        assert run_once() is False


@pytest.mark.parametrize(
    "revision,attempts,expected", [(2, 0, "superseded"), (1, 3, "failed")]
)
def test_stale_or_exhausted_job(revision, attempts, expected):
    db = MagicMock()
    job = NS(id="j", cell_id="c", revision=1, attempts=attempts, status="queued")
    cell = NS(revision=revision, status="queued")
    db.scalar.return_value = job
    db.get.return_value = cell
    client = MagicMock()
    with patch("app.workers.research.SessionLocal", return_value=session(db)):
        assert run_once(client)
    assert job.status == expected
    client.research.assert_not_called()


@pytest.mark.parametrize(
    "success,attempts,expected",
    [(True, 0, "completed"), (False, 0, "queued"), (False, 2, "failed")],
)
def test_completion_and_retries(success, attempts, expected):
    first, second = MagicMock(), MagicMock()
    job = NS(
        id="j",
        cell_id="c",
        revision=1,
        attempts=attempts,
        payload={"question": "Fees"},
        status="queued",
    )
    cell = NS(revision=1, status="queued")
    first.scalar.return_value = job
    first.get.return_value = cell
    second.scalar.side_effect = [job, cell]
    client = MagicMock()
    if success:
        client.research.return_value = AgentResult(answer="Answer", sources=[])
    else:
        client.research.side_effect = TimeoutError("secret provider details")
    with patch(
        "app.workers.research.SessionLocal",
        side_effect=[session(first), session(second)],
    ):
        assert run_once(client)
    assert cell.status == expected and job.status == expected
    if success:
        assert cell.value == "Answer" and cell.sources == []


def test_late_result_cannot_overwrite_edit():
    first, second = MagicMock(), MagicMock()
    job = NS(id="j", cell_id="c", revision=1, attempts=0, payload={}, status="queued")
    cell = NS(revision=1, status="queued", value="newer value")
    first.scalar.return_value = job
    first.get.return_value = cell
    second.scalar.side_effect = [job, cell]
    client = MagicMock()

    def changed(_):
        cell.revision = 2
        return AgentResult(answer="obsolete")

    client.research.side_effect = changed
    with patch(
        "app.workers.research.SessionLocal",
        side_effect=[session(first), session(second)],
    ):
        run_once(client)
    assert job.status == "superseded" and cell.value == "newer value"
