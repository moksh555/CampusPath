"""Fake only external model/web responses; use real LangChain agents and tools."""

import asyncio
import json
import os
import time

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.tools import tool


def event(kind, payload):
    path = os.environ["FIXTURE_EVENTS"]
    with open(path, "a") as output:
        output.write(
            json.dumps(
                dict(
                    kind=kind,
                    pair=[payload["country"], payload["question"]],
                    at=time.monotonic(),
                )
            )
            + "\n"
        )


class FixtureModel(BaseChatModel):
    @property
    def _llm_type(self):
        return "integration-fixture"

    def bind_tools(self, tools, **kwargs):
        return self

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        return self.response(messages)

    async def _agenerate(self, messages, stop=None, run_manager=None, **kwargs):
        await asyncio.sleep(0.02)
        return self.response(messages)

    def response(self, messages):
        payload = json.loads(
            next(
                message.content
                for message in messages
                if isinstance(message, HumanMessage)
            )
        )
        results = [message for message in messages if isinstance(message, ToolMessage)]
        if not results:
            event("start", payload)
            name, args = "get_current_date_and_time", {}
        elif results[-1].name == "get_current_date_and_time":
            name, args = (
                "tavily_search",
                {"query": payload["university"] + " " + payload["question"]},
            )
        elif results[-1].name == "tavily_search":
            name, args = "tavily_extract", {"urls": ["https://example.edu/verified"]}
        else:
            event("end", payload)
            if (
                os.environ.get("FIXTURE_MODE") == "no_content"
                and payload["country"] == "France"
                and payload["question"] == "Courses"
            ):
                raise ValueError("No content found: DO_NOT_PERSIST_PROVIDER_DETAILS")
            name, args = (
                "AgentResult",
                dict(
                    answer=f"Verified {payload['country']} {payload['major']} {payload['question']}",
                    sources=[
                        dict(title="Official", url="https://example.edu/verified")
                    ],
                ),
            )
        return ChatResult(
            generations=[
                ChatGeneration(
                    message=AIMessage(
                        content="",
                        tool_calls=[
                            dict(name=name, args=args, id=f"call-{len(results)}")
                        ],
                    )
                )
            ]
        )


@tool("tavily_search")
def search(query: str) -> dict:
    """Deterministic replacement for external search."""
    return {
        "results": [
            {
                "url": "https://example.edu/verified",
                "content": "Verified fixture information",
            }
        ]
    }


@tool("tavily_extract")
def extract(urls: list[str]) -> dict:
    """Deterministic replacement for external page extraction."""
    return {
        "results": [
            {"url": url, "raw_content": "Verified fixture page"} for url in urls
        ]
    }


async def research(payload):
    import langchain.agents
    from app.agent.agent import research as coordinate
    from app.tools import web

    original = langchain.agents.create_agent

    def create_agent(*args, **kwargs):
        kwargs["model"] = FixtureModel()
        return original(*args, **kwargs)

    langchain.agents.create_agent = create_agent
    web.build_web_tools = lambda: [search, extract]
    return await coordinate(payload)
