from datetime import datetime
from pydantic import BaseModel
from app.db.models.integration import IntegrationProvider, IntegrationStatus


class ConnectRequest(BaseModel):
    webhook_url: str | None = None


class SaveKeysRequest(BaseModel):
    google_client_id: str | None = None
    google_client_secret: str | None = None
    gemini_api_key: str | None = None


class AuthUrlResponse(BaseModel):
    auth_url: str
    provider: str


class IntegrationResponse(BaseModel):
    provider: IntegrationProvider
    name: str
    description: str
    icon: str
    status: IntegrationStatus
    connected_at: datetime | None = None
    n8n_webhook_url: str | None = None
    has_oauth_config: bool = False


class ConnectResultResponse(BaseModel):
    provider: str
    status: IntegrationStatus
    n8n_triggered: bool
    message: str
