"""All runtime configuration. Secrets are never read in feature modules."""

from pathlib import Path

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env", extra="ignore"
    )
    database_url: str = "postgresql+psycopg://localhost/campuspath"
    frontend_origin: str = "http://localhost:3000"
    auth_service_url: str = "http://localhost:8001"
    platform_service_token: SecretStr = SecretStr("")
    research_service_token: SecretStr = SecretStr("")
    university_directory_url: str = "https://raw.githubusercontent.com/Hipo/university-domains-list/master/world_universities_and_domains.json"

    @field_validator("database_url")
    @classmethod
    def postgres_url(cls, value: str) -> str:
        if value.startswith("postgresql://"):
            return value.replace("postgresql://", "postgresql+psycopg://", 1)
        if not value.startswith("postgresql+psycopg://"):
            raise ValueError("Use a PostgreSQL connection string")
        return value


settings = Settings()
