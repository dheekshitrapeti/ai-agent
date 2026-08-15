from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.db.models.activity import ActivitySource, ActivityType


class ActivityCreate(BaseModel):
    source: ActivitySource
    activity_type: ActivityType
    external_id: str = Field(min_length=1, max_length=512)
    title: str | None = Field(default=None, max_length=500)
    sender: str | None = Field(default=None, max_length=500)
    summary: str | None = None
    original_content: str | None = None
    source_url: str | None = None
    event_created_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ActivityResponse(ActivityCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    processed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
