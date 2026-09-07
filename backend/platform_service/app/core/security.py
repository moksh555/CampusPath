"""Platform authorization enforcement through the independent auth service."""

from fastapi import HTTPException, Request

from app.configuration.settings import settings
from app.integrations.identity import authorize


def check_origin(request: Request):
    if request.headers.get("origin") != settings.frontend_origin:
        raise HTTPException(403, "Untrusted request origin")


def get_current_user_id(request: Request) -> str:
    if request.method not in ("GET", "HEAD", "OPTIONS"):
        check_origin(request)
    token = request.cookies.get("access_token", "")
    if not token:
        raise HTTPException(401, "Please sign in")
    action = (
        "platform:read"
        if request.method in ("GET", "HEAD", "OPTIONS")
        else "platform:write"
    )
    return authorize(token, action)
