"""CampusPath research graph; importing this module never calls a provider."""

import json

from app.integrations.agent.client import AgentResult
from app.integrations.agent.system_prompt import SYSTEM_PROMPT


def build_agent():
    from langchain.agents import create_agent
    from langchain.agents.structured_output import ToolStrategy

    from app.integrations.agent.tools.general_tools import get_current_date_and_time_tool
    from app.integrations.agent.tools.web_search_tools import build_web_tools

    return create_agent(
        model="claude-sonnet-4-6",
        system_prompt=SYSTEM_PROMPT,
        tools=[get_current_date_and_time_tool, *build_web_tools()],
        response_format=ToolStrategy(AgentResult),
    )


def research(payload: dict) -> dict:
    result = build_agent().invoke({
        "messages": [{"role": "user", "content": json.dumps(payload)}]
    })
    return AgentResult.model_validate(result["structured_response"]).model_dump(mode="json")
