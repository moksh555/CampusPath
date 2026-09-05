"""All runtime configuration. Secrets are never read in feature modules."""

from pathlib import Path

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env", extra="ignore"
    )
    database_url: str = "postgresql+psycopg://localhost/campuspath"
    frontend_origin: str = "http://localhost:3000"
    google_client_id: str = ""
    google_client_secret: SecretStr = SecretStr("")
    google_redirect_uri: str = "http://localhost:8000/auth/callback"
    jwt_signing_key: SecretStr = SecretStr("")
    cookie_secure: bool = False
    access_minutes: int = Field(default=15, ge=1, le=60)
    refresh_days: int = Field(default=30, ge=1, le=90)
    agent_entrypoint: str = "app.integrations.agent.agent_graph:research"
    agent_python_path: str = ""
    anthropic_api_key: SecretStr = SecretStr("")
    tavily_api_key: SecretStr = SecretStr("")
    agent_timeout_seconds: int = Field(default=120, ge=1, le=600)
    university_directory_url: str = "https://raw.githubusercontent.com/Hipo/university-domains-list/master/world_universities_and_domains.json"

    @field_validator("database_url")
    @classmethod
    def postgres_url(cls, value: str) -> str:
        if value.startswith("postgresql://"):
            return value.replace("postgresql://", "postgresql+psycopg://", 1)
        if not value.startswith("postgresql+psycopg://"):
            raise ValueError("Use a PostgreSQL connection string")
        return value

    def signing_key(self) -> str:
        key = self.jwt_signing_key.get_secret_value()
        if len(key) < 32:
            raise ValueError("JWT_SIGNING_KEY must contain at least 32 characters")
        return key


settings = Settings()
