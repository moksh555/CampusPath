from fastapi.testclient import TestClient

from app.main import app


def test_platform_routes_are_registered_without_auth_endpoints():
    paths = app.openapi()["paths"]
    for path in ["/chats", "/chats/{chat_id}/research", "/colleges/directory"]:
        assert path in paths
    assert not any(path.startswith("/auth/") for path in paths)


def test_health():
    assert TestClient(app).get("/health").json() == {"status": "ok"}


def test_platform_mutations_require_origin():
    assert TestClient(app).post("/chats", json={}).status_code == 403
