"""Worldwide lookup from Hipo's HTTPS dataset, cached for up to one hour."""

from functools import lru_cache
from time import monotonic

import httpx

from app.configuration.settings import settings
from app.schemas.college import CollegeSearchResult

MAX_RESULTS = 12


@lru_cache(maxsize=2)
def _load(url: str, cache_window: int) -> tuple[tuple[str, str | None], ...]:
    """The time-window key expires cached directory data without a scheduler."""
    with httpx.Client(timeout=15.0) as client:
        response = client.get(url)
        response.raise_for_status()
        payload = response.json()
    if not isinstance(payload, list):
        raise ValueError("Invalid university dataset")
    seen = set()
    rows = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        name = item.get("name")
        if not isinstance(name, str) or not name.strip() or len(name.strip()) > 500:
            continue
        name = name.strip()
        country = item.get("country")
        country = country.strip() if isinstance(country, str) else None
        country = country if country and len(country) <= 255 else None
        key = (name.casefold(), (country or "").casefold())
        if key not in seen:
            seen.add(key)
            rows.append((name, country))
    return tuple(rows)


def search(query: str) -> list[CollegeSearchResult]:
    terms = query.casefold().split()
    if not terms:
        return []
    rows = _load(settings.university_directory_url, int(monotonic() // 3600))
    matches = [
        (name, country)
        for name, country in rows
        if all(term in (name + " " + (country or "")).casefold() for term in terms)
    ]
    matches.sort(
        key=lambda row: (
            not row[0].casefold().startswith(query.casefold().strip()),
            row[0].casefold(),
        )
    )
    return [
        CollegeSearchResult(name=name, country=country)
        for name, country in matches[:MAX_RESULTS]
    ]


def list_universities() -> list[CollegeSearchResult]:
    """Return the complete normalized directory for browser-side search."""
    rows = _load(settings.university_directory_url, int(monotonic() // 3600))
    return [CollegeSearchResult(name=name, country=country) for name, country in rows]
