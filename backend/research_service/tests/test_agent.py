import asyncio
import json
import subprocess
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from app.contracts import AgentResult, CellResearchResult, SessionResult
from app.runtime.errors import ResearchFailure
from app.runtime.executor import AgentExecutor
from app.runtime.runner import invoke
from app.settings import settings
from pydantic import ValidationError


def result_for(payload):
    return SessionResult(
        cells=[
            CellResearchResult(
                **target.model_dump(), status="completed", answer="Verified"
            )
            for target in payload.targets
        ]
    )


@pytest.mark.parametrize("answer", ["", " ", None])
def test_empty_answer_rejected(answer):
    with pytest.raises(ValidationError):
        AgentResult(answer=answer)


def test_real_coordinator_dispatches_parallel_units_and_preserves_ids(
    monkeypatch, payload
):
    from app.agent import sub_agent
    from app.agent.agent import research

    active, peak = 0, 0
    calls = []

    async def run(request):
        nonlocal active, peak
        value = json.loads(request["messages"][0]["content"])
        calls.append(value)
        active += 1
        peak = max(peak, active)
        await asyncio.sleep(0.02)
        active -= 1
        return {
            "structured_response": {
                "answer": value["major"] + " " + value["question"],
                "sources": [],
            }
        }

    monkeypatch.setattr(
        sub_agent, "build_subagent", lambda: SimpleNamespace(ainvoke=run)
    )
    result = SessionResult.model_validate(
        asyncio.run(research(payload.model_dump(mode="json")))
    )
    result.validate_for(payload)
    assert peak == 4
    assert len(calls) == 4
    assert {cell.answer for cell in result.cells} == {
        "CS Fees",
        "CS Courses",
        "Math Fees",
        "Math Courses",
    }


@pytest.mark.parametrize(
    "output",
    [{}, {"structured_response": None}, {"structured_response": {"answer": " "}}],
)
def test_missing_content_becomes_explicit_cell_failure(monkeypatch, payload, output):
    from app.agent import sub_agent
    from app.agent.agent import research

    async def run(request):
        return output

    monkeypatch.setattr(
        sub_agent, "build_subagent", lambda: SimpleNamespace(ainvoke=run)
    )
    result = asyncio.run(research(payload.model_dump(mode="json")))
    assert len(result["cells"]) == 4
    assert all(
        cell["error_code"] == "no_content" and cell["status"] == "failed"
        for cell in result["cells"]
    )


def test_one_failed_unit_does_not_discard_others(monkeypatch, payload):
    from app.agent import sub_agent
    from app.agent.agent import research

    async def run(request):
        value = json.loads(request["messages"][0]["content"])
        if value["country"] == "France" and value["question"] == "Fees":
            raise ValueError("No content found; secret-provider-token")
        return {"structured_response": {"answer": "Verified"}}

    monkeypatch.setattr(
        sub_agent, "build_subagent", lambda: SimpleNamespace(ainvoke=run)
    )
    result = asyncio.run(research(payload.model_dump(mode="json")))
    assert sum(cell["status"] == "completed" for cell in result["cells"]) == 3
    assert "secret-provider-token" not in json.dumps(result)


def test_session_result_requires_complete_exact_grid(payload):
    result = result_for(payload)
    result.cells.pop()
    with pytest.raises(ValueError):
        result.validate_for(payload)
    result.cells.append(result.cells[0])
    with pytest.raises(ValueError):
        result.validate_for(payload)


def test_real_child_process_batch_protocol(monkeypatch, tmp_path, payload):
    (tmp_path / "fixture_agent.py").write_text(
        "def research(payload):\n    print('diagnostic')\n    return {'cells': [{**t,'status':'completed','answer':'Verified','sources':[]} for t in payload['targets']]}\n"
    )
    monkeypatch.setattr(settings, "agent_entrypoint", "fixture_agent:research")
    monkeypatch.setattr(settings, "agent_python_path", str(tmp_path))
    assert len(AgentExecutor().research(payload.model_dump(mode="json")).cells) == 4


@pytest.mark.parametrize(
    "output,expected", [("", "no_content"), ("{}", "invalid_response")]
)
def test_empty_or_malformed_process_output(monkeypatch, payload, output, expected):
    with patch(
        "app.runtime.executor.subprocess.run",
        return_value=SimpleNamespace(stdout=output),
    ):
        with pytest.raises(ResearchFailure) as error:
            AgentExecutor().research(payload.model_dump(mode="json"))
    assert error.value.code == expected


def test_process_timeout_is_reported(payload):
    with patch(
        "app.runtime.executor.subprocess.run",
        side_effect=subprocess.TimeoutExpired("agent", 1),
    ):
        with pytest.raises(ResearchFailure) as error:
            AgentExecutor().research(payload.model_dump(mode="json"))
    assert error.value.code == "timeout"


@pytest.mark.parametrize("entry", ["", "module", ":func", "module:", "mod:a:b"])
def test_invalid_entrypoint(entry):
    with pytest.raises(ValueError):
        invoke(entry, {})
