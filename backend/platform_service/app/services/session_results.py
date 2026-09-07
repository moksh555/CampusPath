"""One JSON result document on each chat, projected as cells at the API boundary."""

from copy import deepcopy
from uuid import NAMESPACE_URL, uuid5

ERROR_MESSAGES = {
    "no_content": "The research agent returned no content. Retry this research.",
    "invalid_response": "The agent returned an invalid result. Retry this research.",
    "provider_error": "The research provider could not complete this answer.",
    "timeout": "Research timed out. Retry this research.",
    "agent_error": "The research process failed. Check the research service configuration.",
}


def empty_cell(row_id, column_id):
    return dict(
        id=str(uuid5(NAMESPACE_URL, f"campuspath:{row_id}:{column_id}")),
        column_id=str(column_id),
        value="",
        status="empty",
        sources=[],
        researched_at=None,
        error_code=None,
        error_message=None,
    )


def row_cells(chat, row_id):
    stored = (chat.research_results or {}).get(str(row_id), {})
    return [
        dict(stored.get(str(column.id), empty_cell(row_id, column.id)))
        for column in chat.columns
    ]


def document(chat):
    return deepcopy(chat.research_results or {})


def invalidate(chat, row_id=None, *, content_changed=True):
    chat.research_revision = (chat.research_revision or 0) + 1
    result = document(chat)
    for row_key, cells in result.items():
        for cell in cells.values():
            if (content_changed and (row_id is None or row_key == str(row_id))) or cell[
                "status"
            ] in ("queued", "running"):
                cell["status"] = "stale"
                cell["error_code"] = cell["error_message"] = None
    chat.research_results = result


def remove_row(chat, row_id):
    invalidate(chat, content_changed=False)
    result = document(chat)
    result.pop(str(row_id), None)
    chat.research_results = result


def remove_column(chat, column_id):
    invalidate(chat, content_changed=False)
    result = document(chat)
    for cells in result.values():
        cells.pop(str(column_id), None)
    chat.research_results = result
