"""Authenticated service-to-service queue endpoints; never use browser credentials."""

import secrets
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Response

from app.api.deps import DbSession
from app.configuration.settings import settings
from app.modules.research.contracts import ClaimedJob, ClaimRequest, Completion
from app.services import research_queue


def require_service(authorization: Annotated[str | None, Header()] = None):
    token = settings.research_service_token.get_secret_value()
    if len(token) < 32:
        raise HTTPException(503, "Research service authentication is not configured")
    if not secrets.compare_digest(
        (authorization or "").encode(), ("Bearer " + token).encode()
    ):
        raise HTTPException(401, "Invalid research service credentials")


router = APIRouter(
    prefix="/internal/research/v2",
    tags=["research-service"],
    dependencies=[Depends(require_service)],
)


@router.post(
    "/claim", response_model=ClaimedJob, responses={204: {"description": "No job"}}
)
def claim(request: ClaimRequest, db: DbSession):
    job = research_queue.claim(db, request.timeout_seconds)
    return job if job is not None else Response(status_code=204)


@router.post("/jobs/{job_id}/complete", status_code=204)
def complete(job_id: UUID, request: Completion, db: DbSession):
    try:
        accepted = research_queue.complete(db, job_id, request)
    except ValueError as exc:
        raise HTTPException(422, "Result does not match the session snapshot") from exc
    if not accepted:
        raise HTTPException(409, "Job is no longer owned by this attempt")
    return Response(status_code=204)
