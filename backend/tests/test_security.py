from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock

import jwt
import pytest
from fastapi import HTTPException
from pydantic import SecretStr

from app.configuration.settings import Settings, settings
from app.modules.auth.service import (
    access_token,
    decode_access,
    digest,
    issue_refresh,
    now,
    rotate,
)


@pytest.fixture(autouse=True)
def key(monkeypatch):
    monkeypatch.setattr(
        settings,
        "jwt_signing_key",
        SecretStr("unit-test-only-key-which-is-at-least-32-characters"),
    )


def test_config_normalizes_postgres():
    assert (
        Settings(_env_file=None, database_url="postgresql://host/db").database_url
        == "postgresql+psycopg://host/db"
    )
    with pytest.raises(ValueError):
        Settings(_env_file=None, database_url="mongodb://host/db")


def test_missing_signing_key_fails():
    with pytest.raises(ValueError):
        Settings(_env_file=None, jwt_signing_key="").signing_key()


def test_access_roundtrip_and_signature():
    token = access_token(SimpleNamespace(user_id="u1", id="s1"))
    assert decode_access(token)["sub"] == "u1"
    with pytest.raises(HTTPException):
        decode_access(token + "tampered")


@pytest.mark.parametrize(
    "changes",
    [
        {"exp": now() - timedelta(seconds=1)},
        {"aud": "other"},
        {"iss": "other"},
        {"sid": None},
    ],
)
def test_invalid_claims(changes):
    claims = {
        "sub": "u",
        "sid": "s",
        "iss": "campuspath",
        "aud": "campuspath-api",
        "iat": now(),
        "exp": now() + timedelta(minutes=1),
    }
    claims.update(changes)
    if changes.get("sid", "x") is None:
        del claims["sid"]
    with pytest.raises(HTTPException):
        decode_access(jwt.encode(claims, settings.signing_key(), algorithm="HS256"))


def test_refresh_is_hashed():
    db = MagicMock()
    raw = issue_refresh(db, SimpleNamespace(id="s"))
    assert len(raw) > 40
    assert db.add.call_args.args[0].digest == digest(raw)
    assert db.add.call_args.args[0].digest != raw


@pytest.mark.parametrize(
    "used,revoked,expired",
    [(True, False, False), (False, True, False), (False, False, True)],
)
def test_refresh_rejects_and_revokes_replay(used, revoked, expired):
    db = MagicMock()
    session = SimpleNamespace(
        id="s", revoked=revoked, expires_at=now() + timedelta(days=-1 if expired else 1)
    )
    db.scalar.side_effect = [SimpleNamespace(used=used, session_id="s"), session]
    with pytest.raises(HTTPException):
        rotate(db, "secret")
    if used:
        assert session.revoked and db.commit.called


def test_refresh_rotation():
    db = MagicMock()
    token = SimpleNamespace(used=False, session_id="s")
    session = SimpleNamespace(
        id="s", revoked=False, expires_at=now() + timedelta(days=1)
    )
    db.scalar.side_effect = [token, session]
    result, new_token = rotate(db, "old")
    assert token.used and result is session and new_token != "old"
    assert db.commit.called


def test_unknown_refresh():
    db = MagicMock()
    db.scalar.return_value = None
    with pytest.raises(HTTPException):
        rotate(db, "unknown")
