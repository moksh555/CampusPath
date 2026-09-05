from datetime import timedelta
from types import SimpleNamespace as NS
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from app.configuration.settings import settings
from app.core.database import get_db
from app.main import app
from app.modules.auth.service import now


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(settings, "google_client_id", "test-client")
    monkeypatch.setattr(settings, "google_client_secret", SecretStr("test-only"))
    monkeypatch.setattr(
        settings,
        "jwt_signing_key",
        SecretStr("a-test-only-signing-key-of-more-than-32-characters"),
    )
    db = MagicMock()
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app, follow_redirects=False) as api:
        yield api, db
    app.dependency_overrides.clear()


def test_login_sets_state_and_nonce(client):
    api, db = client
    response = api.get("/auth/login")
    assert response.status_code == 307
    assert response.headers["location"].startswith("https://accounts.google.com/")
    assert "nonce=" in response.headers["location"]
    assert "HttpOnly" in response.headers["set-cookie"]
    assert db.add.called and db.commit.called


def test_missing_google_configuration(client, monkeypatch):
    monkeypatch.setattr(settings, "google_client_id", "")
    assert client[0].get("/auth/login").status_code == 503


def test_state_mismatch(client):
    api, _ = client
    api.cookies.set("oauth_state", "expected")
    assert api.get("/auth/callback?state=wrong&code=code").status_code == 400


@pytest.mark.parametrize("nonce,verified", [("wrong", True), ("nonce", False)])
def test_callback_rejects_invalid_identity(client, nonce, verified):
    api, db = client
    api.cookies.set("oauth_state", "state")
    db.scalar.return_value = NS(nonce="nonce", expires_at=now() + timedelta(minutes=1))
    with (
        patch("app.modules.auth.router.httpx.post") as post,
        patch("app.modules.auth.router.keys.get_signing_key_from_jwt"),
        patch("app.modules.auth.router.jwt.decode") as decode,
    ):
        post.return_value.json.return_value = {"id_token": "test"}
        decode.return_value = {"nonce": nonce, "email_verified": verified}
        assert api.get("/auth/callback?state=state&code=code").status_code == 400


def test_logout_revokes_family(client):
    api, db = client
    login = NS(revoked=False)
    db.get.side_effect = [NS(session_id="s"), login]
    response = api.post("/auth/logout", headers={"Origin": settings.frontend_origin})
    assert response.status_code == 200 and login.revoked
    assert "Max-Age=0" in response.headers["set-cookie"]


def test_successful_google_callback_issues_application_cookies(client):
    api, db = client
    api.cookies.set("oauth_state", "state")
    db.scalar.side_effect = [
        NS(nonce="nonce", expires_at=now() + timedelta(minutes=1)),
        NS(id="user-id"),
    ]

    def assign_id():
        db.add.call_args.args[0].id = "session-id"

    db.flush.side_effect = assign_id
    with (
        patch("app.modules.auth.router.httpx.post") as post,
        patch("app.modules.auth.router.keys.get_signing_key_from_jwt"),
        patch("app.modules.auth.router.jwt.decode") as decode,
    ):
        post.return_value.json.return_value = {"id_token": "test"}
        decode.return_value = {
            "nonce": "nonce",
            "email_verified": True,
            "sub": "google-sub",
            "email": "student@example.test",
        }
        response = api.get("/auth/callback?state=state&code=code")
    assert response.status_code == 307
    assert response.headers["location"] == settings.frontend_origin
    cookies = response.headers.get_list("set-cookie")
    assert any("access_token=" in value and "HttpOnly" in value for value in cookies)
    assert any("refresh_token=" in value and "HttpOnly" in value for value in cookies)
