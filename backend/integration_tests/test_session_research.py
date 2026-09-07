"""End-to-end auth → platform → worker → coordinator → subagents → PostgreSQL."""

import json
import subprocess
import uuid
from concurrent.futures import ThreadPoolExecutor

import httpx
import pytest
from conftest import BACKEND
from sqlalchemy import create_engine, text

WORKER = """
import httpx
from app.settings import settings
from app.clients.platform import PlatformClient
from app.worker import run_once
with httpx.Client(base_url=settings.platform_service_url,headers={'Authorization':'Bearer '+settings.research_service_token.get_secret_value()},timeout=30) as http:
    assert run_once(PlatformClient(http))
"""


@pytest.mark.parametrize("mode", ["complete", "no_content"])
def test_all_services_session_batch(client, services, mode):
    response = client.post(
        "/chats",
        json={
            "title": "integration-" + str(uuid.uuid4()),
            "major": "CS",
            "colleges": [
                {"name": "Example", "country": "Canada"},
                {"name": "Example", "country": "France", "major_override": "Math"},
            ],
            "columns": ["Fees", "Courses"],
        },
    )
    assert response.status_code == 201, response.text
    chat = response.json()
    path = "/chats/" + chat["id"]
    events = services["directory"] / (mode + "-events.jsonl")
    try:
        with httpx.Client(
            base_url=services["platform_url"],
            cookies={"access_token": services["identities"][1]["token"]},
            timeout=15,
        ) as stranger:
            assert stranger.get(path).status_code == 404
        with ThreadPoolExecutor(max_workers=2) as pool:
            queued = list(
                pool.map(lambda _: client.post(path + "/research").json(), range(2))
            )
        assert sorted(result["queued"] for result in queued) == [0, 1]
        assert sum(result["cells"] for result in queued) == 4
        env = {**services["env"], "FIXTURE_EVENTS": str(events), "FIXTURE_MODE": mode}
        for attempt in range(1, 4 if mode == "no_content" else 2):
            subprocess.run(
                [str(BACKEND / "research_service/.venv/bin/python"), "-c", WORKER],
                cwd=BACKEND / "research_service",
                env=env,
                check=True,
                timeout=90,
            )
            current = client.get(path).json()
            cells = [cell for row in current["colleges"] for cell in row["cells"]]
            assert sum(cell["status"] == "completed" for cell in cells) == (
                3 if mode == "no_content" else 4
            ), cells
            if mode == "no_content":
                failed = next(cell for cell in cells if cell["status"] != "completed")
                assert failed["error_code"] == "no_content"
                assert failed["status"] == ("failed" if attempt == 3 else "queued")
                assert "no content" in failed["error_message"]
                assert "DO_NOT_PERSIST" not in json.dumps(current)
        url = services["urls"]["platform_service"].replace(
            "postgresql://", "postgresql+psycopg://", 1
        )
        engine = create_engine(url)
        with engine.connect() as db:
            assert (
                db.scalar(
                    text(
                        "SELECT count(*) FROM platform.research_jobs WHERE chat_id=:id"
                    ),
                    {"id": chat["id"]},
                )
                == 1
            )
            document = db.scalar(
                text("SELECT research_results FROM platform.chats WHERE id=:id"),
                {"id": chat["id"]},
            )
            assert sum(len(row) for row in document.values()) == 4
            assert db.scalar(text("SELECT to_regclass('platform.cells')")) is None
            job = (
                db.execute(
                    text(
                        "SELECT id,revision,attempts,status FROM platform.research_jobs WHERE chat_id=:id"
                    ),
                    {"id": chat["id"]},
                )
                .mappings()
                .one()
            )
        engine.dispose()
        assert job["status"] == ("failed" if mode == "no_content" else "completed")
        records = [json.loads(line) for line in events.read_text().splitlines()]
        active = peak = 0
        for record in records:
            active += 1 if record["kind"] == "start" else -1
            peak = max(peak, active)
        assert peak == 4
        starts = [record["pair"] for record in records if record["kind"] == "start"]
        assert len(starts) == (6 if mode == "no_content" else 4)
        if mode == "no_content":
            assert starts.count(["France", "Courses"]) == 3
        # A late/duplicate completion cannot overwrite the persisted result.
        with httpx.Client(
            base_url=services["platform_url"],
            headers={
                "Authorization": "Bearer " + services["env"]["RESEARCH_SERVICE_TOKEN"]
            },
        ) as worker:
            assert (
                worker.post(
                    f"/internal/research/v2/jobs/{job['id']}/complete",
                    json={
                        "attempt": job["attempts"],
                        "revision": job["revision"],
                        "result": None,
                        "error_code": "no_content",
                    },
                ).status_code
                == 409
            )
        # Editing invalidates the snapshot; rerun reuses the same job row.
        assert client.patch(path, json={"major": "Physics"}).status_code == 200
        assert client.post(path + "/research").json() == {"queued": 1, "cells": 4}
        engine = create_engine(url)
        with engine.connect() as db:
            assert (
                db.scalar(
                    text("SELECT id FROM platform.research_jobs WHERE chat_id=:id"),
                    {"id": chat["id"]},
                )
                == job["id"]
            )
        engine.dispose()
    finally:
        assert client.delete(path).status_code == 204
