from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from app.core.database import get_db
from app.main import app


def test_openapi_routes_are_registered():
    paths = app.openapi()["paths"]
    for path in [
        "/auth/login",
        "/auth/refresh",
        "/auth/me",
        "/chats",
        "/chats/{chat_id}/research",
    ]:
        assert path in paths


def test_health():
    assert TestClient(app).get("/health").json() == {"status": "ok"}


def test_mutations_require_origin():
    app.dependency_overrides[get_db] = lambda: MagicMock()
    try:
        client = TestClient(app)
        assert client.post("/auth/refresh").status_code == 403
        assert (
            client.post(
                "/auth/logout", headers={"Origin": "https://evil.example"}
            ).status_code
            == 403
        )
        assert client.get("/auth/callback?state=wrong&code=bad").status_code == 400
    finally:
        app.dependency_overrides.clear()
