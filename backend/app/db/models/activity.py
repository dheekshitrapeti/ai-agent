from datetime import datetime
from enum import Enum
from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Index, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class ActivitySource(str, Enum):
    SLACK = "slack"
    GMAIL = "gmail"
    GOOGLE_DRIVE = "google_drive"


class ActivityType(str, Enum):
    MESSAGE = "message"
    EMAIL = "email"
    DOCUMENT = "document"


class Activity(Base):
    __tablename__ = "activities"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    source: Mapped[ActivitySource] = mapped_column(SAEnum(ActivitySource, name="activity_source"), nullable=False, index=True)
    activity_type: Mapped[ActivityType] = mapped_column(SAEnum(ActivityType, name="activity_type"), nullable=False, index=True)
    external_id: Mapped[str] = mapped_column(String(512), nullable=False)
    title: Mapped[str | None] = mapped_column(String(500))
    sender: Mapped[str | None] = mapped_column(String(500))
    summary: Mapped[str | None] = mapped_column(Text)
    original_content: Mapped[str | None] = mapped_column(Text)
    source_url: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict | None] = mapped_column(JSON)
    event_created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship("User", back_populates="activities")

    __table_args__ = (
        UniqueConstraint("user_id", "source", "external_id", name="uq_activities_user_source_external_id"),
        Index("ix_activities_user_created_at", "user_id", "created_at"),
        Index("ix_activities_source_event_created_at", "source", "event_created_at"),
    )
