"""Local agent execution within the backend deployment, with a hard timeout."""

import json
import os
import subprocess
import sys
from pathlib import Path

from pydantic import BaseModel, Field, HttpUrl

from app.configuration.settings import settings


class Source(BaseModel):
    title: str = ""
    url: HttpUrl


class AgentResult(BaseModel):
    model_config = {"str_strip_whitespace": True}
    answer: str = Field(min_length=1, max_length=100000)
    sources: list[Source] = Field(default_factory=list)


class AgentClient:
    def research(self, payload: dict) -> AgentResult:
        if not settings.agent_entrypoint:
            raise ValueError("Configure AGENT_ENTRYPOINT in backend/.env")
        env = os.environ.copy()
        for name, secret in (
            ("ANTHROPIC_API_KEY", settings.anthropic_api_key),
            ("TAVILY_API_KEY", settings.tavily_api_key),
        ):
            if secret.get_secret_value():
                env[name] = secret.get_secret_value()
        # A child process bounds execution time without leaving timed-out threads
        # running provider calls after the job lease expires. No network service.
        completed = subprocess.run(
            [sys.executable, "-m", "app.integrations.agent.runner"],
            input=json.dumps({"entrypoint": settings.agent_entrypoint,
                              "python_path": settings.agent_python_path,
                              "payload": payload}),
            capture_output=True, text=True, env=env,
            cwd=Path(__file__).resolve().parents[3],
            timeout=settings.agent_timeout_seconds, check=True,
        )
        return AgentResult.model_validate_json(completed.stdout)
