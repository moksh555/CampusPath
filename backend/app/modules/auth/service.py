"""Token creation and rotation, independent of HTTP response handling."""

import hashlib
import secrets
from datetime import UTC, datetime, timedelta

import jwt
from fastapi import HTTPException
from sqlalchemy import select

from app.configuration.settings import settings
from app.modules.auth.models import LoginSession, RefreshToken


def now():
    return datetime.now(UTC)


def digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def access_token(session: LoginSession) -> str:
    return jwt.encode(
        {
            "sub": session.user_id,
            "sid": session.id,
            "iss": "campuspath",
            "aud": "campuspath-api",
            "iat": now(),
            "exp": now() + timedelta(minutes=settings.access_minutes),
        },
        settings.signing_key(),
        algorithm="HS256",
    )


def decode_access(value: str) -> dict:
    try:
        return jwt.decode(
            value,
            settings.signing_key(),
            algorithms=["HS256"],
            issuer="campuspath",
            audience="campuspath-api",
            options={"require": ["sub", "sid", "exp", "iat"]},
        )
    except (jwt.PyJWTError, ValueError) as exc:
        raise HTTPException(401, "Session expired. Please sign in.") from exc


def issue_refresh(db, session):
    value = secrets.token_urlsafe(48)
    db.add(RefreshToken(digest=digest(value), session_id=session.id))
    return value


def rotate(db, value):
    token = db.scalar(
        select(RefreshToken)
        .where(RefreshToken.digest == digest(value))
        .with_for_update()
    )
    if token is None:
        raise HTTPException(401, "Invalid refresh token")
    session = db.scalar(
        select(LoginSession)
        .where(LoginSession.id == token.session_id)
        .with_for_update()
    )
    if token.used:
        session.revoked = True
        db.commit()
        raise HTTPException(401, "Refresh token reused; sign in again")
    if session.revoked or session.expires_at <= now():
        raise HTTPException(401, "Session expired")
    token.used = True
    fresh = issue_refresh(db, session)
    db.commit()
    return session, fresh
