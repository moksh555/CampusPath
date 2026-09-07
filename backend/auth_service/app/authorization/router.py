"""Private session validation and authorization API for the platform service."""

import secrets
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Response
from pydantic import BaseModel, Field, SecretStr

from app.authorization.policy import authorize
from app.configuration.settings import settings
from app.core.database import get_db
from app.core.security import validate_session


def require_platform(authorization: Annotated[str | None, Header()] = None):
    token = settings.platform_service_token.get_secret_value()
    if len(token) < 32:
        raise HTTPException(503, "Platform authentication is not configured")
    if not secrets.compare_digest(
        (authorization or "").encode(), ("Bearer " + token).encode()
    ):
        raise HTTPException(401, "Invalid service credentials")


class AuthorizationRequest(BaseModel):
    access_token: SecretStr
    action: str = Field(max_length=100)
    owner_id: str | None = Field(default=None, max_length=255)


class AuthorizationDecision(BaseModel):
    user_id: str
    allowed: bool


router = APIRouter(
    prefix="/internal/auth/v1",
    tags=["authorization"],
    dependencies=[Depends(require_platform)],
)


@router.post("/authorize", response_model=AuthorizationDecision)
def authorize_request(
    request: AuthorizationRequest, response: Response, db=Depends(get_db)
):
    user_id = validate_session(request.access_token.get_secret_value(), db)
    authorize(user_id, request.action, request.owner_id)
    response.headers["Cache-Control"] = "no-store"
    return AuthorizationDecision(user_id=user_id, allowed=True)
