"""Build one independent research subagent per table cell, without import-time calls."""

import json

from app.contracts import AgentResult
from app.prompts.research_prompt import RESEARCH_SYSTEM_PROMPT
from app.runtime.errors import ResearchFailure


def build_subagent():
    from langchain.agents import create_agent
    from langchain.agents.structured_output import ToolStrategy

    from app.tools.date import get_current_date_and_time_tool
    from app.tools.web import build_web_tools

    return create_agent(
        model="claude-sonnet-4-6",
        system_prompt=RESEARCH_SYSTEM_PROMPT,
        tools=[get_current_date_and_time_tool, *build_web_tools()],
        response_format=ToolStrategy(AgentResult),
    )


async def research_unit(payload: dict) -> AgentResult:
    output = await build_subagent().ainvoke(
        {"messages": [{"role": "user", "content": json.dumps(payload)}]}
    )
    structured = output.get("structured_response") if isinstance(output, dict) else None
    if structured is None:
        raise ResearchFailure("no_content")
    if isinstance(structured, dict) and not str(structured.get("answer") or "").strip():
        raise ResearchFailure("no_content")
    return AgentResult.model_validate(structured)
