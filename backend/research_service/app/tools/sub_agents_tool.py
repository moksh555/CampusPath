"""Typed subagent capability used by the session coordinator."""

from langchain.tools import tool

from app.agent.sub_agent import research_unit


@tool("unit_level_research")
async def unit_level_research(
    university: str, country: str | None, major: str | None, question: str
) -> dict:
    """Research one university/question pair and return its verified answer and sources."""
    return (
        await research_unit(
            dict(university=university, country=country, major=major, question=question)
        )
    ).model_dump(mode="json")
