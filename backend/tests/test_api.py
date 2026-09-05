"""Real PostgreSQL contract tests; use a disposable TEST_DATABASE_URL branch."""

import os

import pytest

if not os.environ.get("TEST_DATABASE_URL"):
    pytest.skip(
        "Set TEST_DATABASE_URL to a disposable PostgreSQL branch",
        allow_module_level=True,
    )
os.environ["DATABASE_URL"] = os.environ["TEST_DATABASE_URL"]
from fastapi.testclient import TestClient

from app.core.database import engine
from app.core.security import get_current_user_id
from app.main import app
from app.models import Base


@pytest.fixture
def client():
    Base.metadata.create_all(engine)
    user = {"id": "test-a"}
    app.dependency_overrides[get_current_user_id] = lambda: user["id"]
    with TestClient(app) as value:
        yield value, user
    app.dependency_overrides.clear()


def test_comparison_lifecycle(client):
    api, user = client
    created = api.post(
        "/chats",
        json={
            "colleges": [{"name": "Example University"}],
            "columns": ["Annual fees", "CS ranking"],
        },
    )
    assert created.status_code == 201, created.text
    chat = created.json()
    path = "/chats/" + chat["id"]
    try:
        assert len(chat["colleges"][0]["cells"]) == 2
        user["id"] = "test-b"
        for method, suffix, body in [
            ("GET", "", None),
            ("PATCH", "", {"title": "stolen"}),
            ("POST", "/colleges", {"name": "stolen"}),
            ("DELETE", "", None),
        ]:
            assert api.request(method, path + suffix, json=body).status_code == 404
        user["id"] = "test-a"
        row = api.post(path + "/colleges", json={"name": "Custom school"}).json()
        assert len(row["cells"]) == 2
        rowpath = path + "/colleges/" + row["id"]
        assert (
            api.patch(rowpath, json={"major_override": "CS"}).json()["major_override"]
            == "CS"
        )
        assert (
            api.patch(rowpath, json={"major_override": None}).json()["major_override"]
            is None
        )
        assert api.patch(path, json={"major": "Math"}).json()["major"] == "Math"
        assert api.patch(path, json={"major": None}).json()["major"] is None
        assert api.post(path + "/columns", json={"label": "   "}).status_code == 422
        assert api.post(path + "/colleges", json={"name": "   "}).status_code == 422
        column = api.post(path + "/columns", json={"label": "Scholarships"}).json()
        assert len(api.get(path).json()["colleges"][0]["cells"]) == 3
        assert api.delete(path + "/columns/" + column["id"]).status_code == 204
        assert len(api.get(path).json()["colleges"][0]["cells"]) == 2
    finally:
        user["id"] = "test-a"
        api.delete(path)
