"""HTTP client for identity policy decisions; no auth database or signing keys."""

import httpx
from fastapi import HTTPException
from pydantic import BaseModel, ValidationError

from app.configuration.settings import settings


class Decision(BaseModel):
    user_id: str
    allowed: bool


def authorize(access_token: str, action: str, owner_id: str | None = None) -> str:
    service_token = settings.platform_service_token.get_secret_value()
    if len(service_token) < 32:
        raise HTTPException(503, "Configure PLATFORM_SERVICE_TOKEN")
    try:
        response = httpx.post(
            settings.auth_service_url.rstrip("/") + "/internal/auth/v1/authorize",
            headers={"Authorization": "Bearer " + service_token},
            json={"access_token": access_token, "action": action, "owner_id": owner_id},
            timeout=5,
        )
        if response.status_code in (401, 403):
            raise HTTPException(
                response.status_code, "Session expired or access denied"
            )
        response.raise_for_status()
        decision = Decision.model_validate(response.json())
        if not decision.allowed or not decision.user_id:
            raise HTTPException(403, "Access denied")
        return decision.user_id
    except (httpx.HTTPError, ValidationError, ValueError) as exc:
        raise HTTPException(503, "Authentication service unavailable") from exc
