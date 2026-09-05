"""/colleges/search — autocomplete over the worldwide university directory."""

import httpx
from fastapi import APIRouter, HTTPException, Query

from app.api.deps import CurrentUserId
from app.schemas.college import CollegeSearchResult
from app.services import college_directory

router = APIRouter(prefix="/colleges", tags=["college-directory"])


@router.get("/search", response_model=list[CollegeSearchResult])
def search_colleges(user_id: CurrentUserId, q: str = Query(min_length=1, max_length=255)):
    try:
        return college_directory.search(q)
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(
            503, "University directory unavailable; enter a university manually"
        ) from exc


@router.get("/directory", response_model=list[CollegeSearchResult])
def university_directory(user_id: CurrentUserId):
    try:
        return college_directory.list_universities()
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(
            503, "University directory unavailable; enter a university manually"
        ) from exc
