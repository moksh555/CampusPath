"""Real HTTP processes + real test PostgreSQL; no fake service or persistence layer."""

import json
import os
import socket
import subprocess
import time
from pathlib import Path

import httpx
import pytest
from dotenv import dotenv_values

BACKEND = Path(__file__).resolve().parents[1]
SEED = """
import json,uuid
from datetime import timedelta
from app.core.database import SessionLocal
from app.authentication.models import User,LoginSession
from app.authentication.service import access_token,now
with SessionLocal() as db:
    result=[]
    for _ in range(2):
        uid=str(uuid.uuid4())
        user=User(id=uid,google_subject='integration-'+uid,email=uid+'@example.test',name='Integration')
        db.add(user); db.flush()
        session=LoginSession(user_id=uid,expires_at=now()+timedelta(hours=1))
        db.add(session);db.flush()
        result.append({'id':uid,'token':access_token(session)})
    db.commit()
    print(json.dumps(result))
"""


def port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@pytest.fixture(scope="session")
def services(tmp_path_factory):
    directory = tmp_path_factory.mktemp("microservices")
    urls = {}
    for service in ["auth_service", "platform_service"]:
        urls[service] = os.environ.get("TEST_DATABASE_URL") or dotenv_values(
            BACKEND / service / ".env.test"
        ).get("TEST_DATABASE_URL")
        if not urls[service]:
            pytest.fail(
                f"Set TEST_DATABASE_URL in {service}/.env.test to run integration tests"
            )
    auth_port, platform_port = port(), port()
    auth_url, platform_url = (
        f"http://127.0.0.1:{auth_port}",
        f"http://127.0.0.1:{platform_port}",
    )
    env = os.environ.copy()
    env.update(
        PLATFORM_SERVICE_TOKEN="integration-platform-" * 3,
        RESEARCH_SERVICE_TOKEN="integration-research-" * 3,
        JWT_SIGNING_KEY="integration-signing-" * 3,
        FRONTEND_ORIGIN="http://frontend.test",
        AUTH_SERVICE_URL=auth_url,
        PLATFORM_SERVICE_URL=platform_url,
        AGENT_ENTRYPOINT="session_fixture:research",
        AGENT_PYTHON_PATH=str(Path(__file__).parent),
        MAX_PARALLEL_UNITS="4",
        AGENT_TIMEOUT_SECONDS="60",
        UNIT_TIMEOUT_SECONDS="20",
        ANTHROPIC_API_KEY="fixture-only",
        TAVILY_API_KEY="fixture-only",
        PYTHONUNBUFFERED="1",
    )
    processes = []
    identities = []
    log = open(directory / "services.log", "w+")
    try:
        for service in ["auth_service", "platform_service"]:
            service_env = {**env, "DATABASE_URL": urls[service]}
            subprocess.run(
                [
                    str(BACKEND / service / ".venv/bin/python"),
                    "-m",
                    "alembic",
                    "upgrade",
                    "head",
                ],
                cwd=BACKEND / service,
                env=service_env,
                check=True,
                timeout=60,
            )
        identities = json.loads(
            subprocess.check_output(
                [str(BACKEND / "auth_service/.venv/bin/python"), "-c", SEED],
                cwd=BACKEND / "auth_service",
                env={**env, "DATABASE_URL": urls["auth_service"]},
                text=True,
                timeout=30,
            )
        )
        for service, server_port in [
            ("auth_service", auth_port),
            ("platform_service", platform_port),
        ]:
            processes.append(
                subprocess.Popen(
                    [
                        str(BACKEND / service / ".venv/bin/python"),
                        "-m",
                        "uvicorn",
                        "app.main:app",
                        "--host",
                        "127.0.0.1",
                        "--port",
                        str(server_port),
                    ],
                    cwd=BACKEND / service,
                    env={**env, "DATABASE_URL": urls[service]},
                    stdout=log,
                    stderr=log,
                )
            )
        with httpx.Client(timeout=15) as http:
            for url in [auth_url, platform_url]:
                deadline = time.monotonic() + 30
                while True:
                    try:
                        if http.get(url + "/health").is_success:
                            break
                    except httpx.HTTPError:
                        pass
                    if time.monotonic() > deadline:
                        pytest.fail(
                            f"Service startup failed; see {directory}/services.log"
                        )
                    time.sleep(0.1)
        yield dict(
            platform_url=platform_url,
            auth_url=auth_url,
            env=env,
            identities=identities,
            directory=directory,
            urls=urls,
        )
    finally:
        for process in processes:
            process.terminate()
        for process in processes:
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
        if identities:
            cleanup = "from app.core.database import SessionLocal; from app.authentication.models import User; import os,json; from sqlalchemy import delete; db=SessionLocal(); db.execute(delete(User).where(User.id.in_(json.loads(os.environ['TEST_USER_IDS'])))); db.commit(); db.close()"
            subprocess.run(
                [str(BACKEND / "auth_service/.venv/bin/python"), "-c", cleanup],
                cwd=BACKEND / "auth_service",
                env={
                    **env,
                    "DATABASE_URL": urls["auth_service"],
                    "TEST_USER_IDS": json.dumps([value["id"] for value in identities]),
                },
                check=True,
                timeout=30,
            )
        log.close()


@pytest.fixture
def client(services):
    with httpx.Client(
        base_url=services["platform_url"],
        timeout=30,
        cookies={"access_token": services["identities"][0]["token"]},
        headers={"Origin": "http://frontend.test"},
    ) as http:
        yield http
