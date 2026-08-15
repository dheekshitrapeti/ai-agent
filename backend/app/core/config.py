from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Workspace Assistant API"
    environment: str = "development"
    api_prefix: str = "/api"
    database_url: str = "postgresql+psycopg://workspace:workspace@localhost:5432/workspace_assistant"
    cors_origins: list[str] = ["http://localhost:3000"]
    n8n_ingest_api_key: str | None = None
    default_user_email: str = "n8n@local"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
