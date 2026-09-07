"""Agent execution within the research microservice, with a hard timeout."""

import json
import os
import subprocess
import sys
from pathlib import Path

from app.contracts import SessionPayload, SessionResult
from app.runtime.errors import ResearchFailure
from app.settings import settings


class AgentExecutor:
    def research(self, payload: dict) -> SessionResult:
        if not settings.agent_entrypoint:
            raise ValueError(
                "Configure AGENT_ENTRYPOINT in backend/research_service/.env"
            )
        env = os.environ.copy()
        for name, secret in (
            ("ANTHROPIC_API_KEY", settings.anthropic_api_key),
            ("TAVILY_API_KEY", settings.tavily_api_key),
        ):
            if secret.get_secret_value():
                env[name] = secret.get_secret_value()
        # A child process bounds execution time without leaving timed-out threads
        # running provider calls after the job lease expires. The agent itself runs inside this service.
        try:
            completed = subprocess.run(
                [sys.executable, "-m", "app.runtime.runner"],
                input=json.dumps(
                    {
                        "entrypoint": settings.agent_entrypoint,
                        "python_path": settings.agent_python_path,
                        "payload": payload,
                    }
                ),
                capture_output=True,
                text=True,
                env=env,
                cwd=Path(__file__).resolve().parents[2],
                timeout=settings.agent_timeout_seconds,
                check=True,
            )
        except subprocess.TimeoutExpired as exc:
            raise ResearchFailure("timeout") from exc
        except subprocess.CalledProcessError as exc:
            raise ResearchFailure("agent_error") from exc
        if not completed.stdout.strip():
            raise ResearchFailure("no_content")
        try:
            return SessionResult.model_validate_json(completed.stdout).validate_for(
                SessionPayload.model_validate(payload)
            )
        except ValueError as exc:
            raise ResearchFailure("invalid_response") from exc
