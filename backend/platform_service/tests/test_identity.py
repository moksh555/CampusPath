from unittest.mock import Mock, patch

import httpx
import pytest
from fastapi import HTTPException
from pydantic import SecretStr

from app.configuration.settings import settings
from app.integrations.identity import authorize


@pytest.fixture(autouse=True)
def configuration(monkeypatch):
    monkeypatch.setattr(
        settings, "platform_service_token", SecretStr("test-platform-token-" * 3)
    )


def test_identity_authorization_is_an_http_boundary():
    response = Mock()
    response.status_code = 200
    response.json.return_value = {"user_id": "student", "allowed": True}
    with patch("app.integrations.identity.httpx.post", return_value=response) as post:
        assert authorize("access-token", "platform:write", "student") == "student"
    assert post.call_args.kwargs["json"]["owner_id"] == "student"
    assert post.call_args.args[0].endswith("/internal/auth/v1/authorize")


@pytest.mark.parametrize("status", [401, 403])
def test_identity_denial_is_enforced(status):
    with patch(
        "app.integrations.identity.httpx.post", return_value=Mock(status_code=status)
    ):
        with pytest.raises(HTTPException) as error:
            authorize("bad", "platform:read")
        assert error.value.status_code == status


def test_identity_outage_fails_closed():
    with patch(
        "app.integrations.identity.httpx.post",
        side_effect=httpx.ConnectError("offline"),
    ):
        with pytest.raises(HTTPException) as error:
            authorize("token", "platform:read")
        assert error.value.status_code == 503
