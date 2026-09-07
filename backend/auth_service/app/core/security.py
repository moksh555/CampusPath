"""Cookie JWT authentication and same-origin protection for mutations."""

from fastapi import Depends, HTTPException, Request

from app.authentication.models import LoginSession
from app.authentication.service import decode_access, now
from app.configuration.settings import settings
from app.core.database import get_db


def check_origin(request: Request):
    if request.headers.get("origin") != settings.frontend_origin:
        raise HTTPException(403, "Untrusted request origin")


def get_current_user_id(request: Request, db=Depends(get_db)) -> str:
    if request.method not in ("GET", "HEAD", "OPTIONS"):
        check_origin(request)
    return validate_session(request.cookies.get("access_token", ""), db)


def validate_session(token: str, db) -> str:
    claims = decode_access(token)
    session = db.get(LoginSession, claims["sid"])
    if (
        not session
        or session.revoked
        or session.expires_at <= now()
        or session.user_id != claims["sub"]
    ):
        raise HTTPException(401, "Session expired")
    return session.user_id
