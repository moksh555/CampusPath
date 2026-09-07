"""Naming rules and the default column set every chat starts with."""

import re

DEFAULT_COLUMNS: tuple[tuple[str, str], ...] = (
    ("prerequisites", "Prerequisites"),
    ("fees", "Fees"),
    ("location", "Location"),
    ("course_description", "Course description"),
)


def slugify(label: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-")
    return slug or "column"


def unique_column_key(label: str, existing_keys: set[str]) -> str:
    base = slugify(label)[:240]
    key = base
    suffix = 2
    while key in existing_keys:
        key = f"{base}-{suffix}"
        suffix += 1
    return key


def build_chat_title(major: str | None, colleges: list) -> str:
    """Name a chat after its colleges, falling back to the major."""
    names = [c.name.strip() for c in colleges if getattr(c, "name", None)]
    if names:
        title = ", ".join(names[:2])
        if len(names) > 2:
            title += f" +{len(names) - 2}"
        return title
    if major and major.strip():
        return major.strip()
    return "Untitled"
