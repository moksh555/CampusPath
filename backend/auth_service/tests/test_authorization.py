from datetime import timedelta
from types import SimpleNamespace as NS
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from app.authentication.service import access_token, now
from app.configuration.settings import settings
from app.core.database import get_db
from app.main import app


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(
        settings, "platform_service_token", SecretStr("platform-token-" * 3)
    )
    monkeypatch.setattr(settings, "jwt_signing_key", SecretStr("signing-key-" * 4))
    session = NS(
        id="session",
        user_id="student",
        revoked=False,
        expires_at=now() + timedelta(days=1),
    )
    db = MagicMock()
    db.get.return_value = session
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as api:
        yield api, session
    app.dependency_overrides.clear()


def authorize(api, session, **changes):
    body = dict(
        access_token=access_token(session), action="platform:read", owner_id="student"
    )
    body.update(changes)
    return api.post(
        "/internal/auth/v1/authorize",
        json=body,
        headers={
            "Authorization": "Bearer "
            + settings.platform_service_token.get_secret_value()
        },
    )


def test_active_session_and_owner_allowed(client):
    api, session = client
    response = authorize(api, session)
    assert response.status_code == 200
    assert response.json() == {"user_id": "student", "allowed": True}
    assert response.headers["cache-control"] == "no-store"


@pytest.mark.parametrize(
    "change", [dict(owner_id="another-student"), dict(action="platform:admin")]
)
def test_policy_denies_other_owners_and_unknown_actions(client, change):
    assert authorize(*client, **change).status_code == 403


@pytest.mark.parametrize("state", ["revoked", "expired"])
def test_revoked_and_expired_sessions_rejected(client, state):
    api, session = client
    if state == "revoked":
        session.revoked = True
    else:
        session.expires_at = now() - timedelta(seconds=1)
    assert authorize(api, session).status_code == 401


def test_missing_service_token_rejected(client):
    assert (
        client[0]
        .post(
            "/internal/auth/v1/authorize",
            json={"access_token": "x", "action": "platform:read"},
        )
        .status_code
        == 401
    )


def test_auth_routes_only(client):
    paths = client[0].get("/openapi.json").json()["paths"]
    assert "/auth/login" in paths and "/auth/me" in paths
    assert "/chats" not in paths
    assert client[0].post("/auth/refresh").status_code == 403


def test_shared_access_cookie_and_private_refresh_cookie(client, monkeypatch):
    from fastapi.responses import JSONResponse

    from app.authentication.router import cookies

    monkeypatch.setattr(settings, "cookie_domain", ".example.test")
    values = cookies(JSONResponse({}), client[1], "refresh").headers.getlist(
        "set-cookie"
    )
    assert "Domain=.example.test" in next(
        v for v in values if v.startswith("access_token=")
    )
    assert "Domain=" not in next(v for v in values if v.startswith("refresh_token="))
