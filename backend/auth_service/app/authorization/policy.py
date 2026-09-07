"""Platform access policy owned by the identity service."""

from fastapi import HTTPException


def authorize(user_id: str, action: str, owner_id: str | None):
    if action not in {"platform:read", "platform:write"}:
        raise HTTPException(403, "Action is not permitted")
    if owner_id is not None and owner_id != user_id:
        raise HTTPException(403, "Resource access denied")
