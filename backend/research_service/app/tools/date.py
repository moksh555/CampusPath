"""Date context for current university research."""

from datetime import datetime

from langchain.tools import tool


@tool("get_current_date_and_time")
def get_current_date_and_time_tool() -> str:
    """Get the current local date, time and timezone."""
    return datetime.now().astimezone().isoformat(timespec="seconds")
