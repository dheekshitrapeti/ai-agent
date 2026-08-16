from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Workspace Assistant API"
    environment: str = "development"
    api_prefix: str = "/api"
    database_url: str = "sqlite:///./workspace.db"
    cors_origins: list[str] = ["http://localhost:3000"]
    n8n_ingest_api_key: str | None = "secret-n8n-key-123"
    n8n_gmail_webhook_url: str = "http://localhost:5678/webhook/gmail-sync"
    default_user_email: str = "n8n@local"
    google_client_id: str | None = None
    google_client_secret: str | None = None
    google_redirect_uri: str = "http://localhost:8000/api/integrations/gmail/callback"
    google_drive_redirect_uri: str = "http://localhost:8000/api/integrations/google_drive/callback"
    slack_client_id: str | None = None
    slack_client_secret: str | None = None
    slack_redirect_uri: str = "http://localhost:8000/api/integrations/slack/callback"
    n8n_slack_webhook_url: str = "http://localhost:5678/webhook/slack-sync"
    n8n_google_drive_webhook_url: str = "http://localhost:5678/webhook/drive-sync"
    gemini_api_key: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


def get_settings() -> Settings:
    return Settings()


settings = get_settings()
