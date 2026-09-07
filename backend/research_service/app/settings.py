"""Independent research service configuration; no database or OAuth credentials."""

from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[1] / ".env", extra="ignore"
    )
    platform_service_url: str = "http://localhost:8000"
    research_service_token: SecretStr = SecretStr("")
    agent_entrypoint: str = "app.agent.agent:research"
    agent_python_path: str = ""
    anthropic_api_key: SecretStr = SecretStr("")
    tavily_api_key: SecretStr = SecretStr("")
    agent_timeout_seconds: int = Field(default=600, ge=1, le=3600)
    unit_timeout_seconds: int = Field(default=120, ge=1, le=600)
    max_parallel_units: int = Field(default=16, ge=1, le=128)
    poll_seconds: float = Field(default=2, ge=0.1, le=60)


settings = Settings()
