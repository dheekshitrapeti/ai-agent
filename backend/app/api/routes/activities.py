from datetime import datetime, timezone
from secrets import compare_digest

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models.activity import Activity
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.activity import ActivityCreate, ActivityResponse

router = APIRouter()


def serialize_activity(activity: Activity) -> ActivityResponse:
    return ActivityResponse(
        id=activity.id,
        source=activity.source,
        activity_type=activity.activity_type,
        external_id=activity.external_id,
        title=activity.title,
        sender=activity.sender,
        summary=activity.summary,
        original_content=activity.original_content,
        source_url=activity.source_url,
        event_created_at=activity.event_created_at,
        metadata=activity.metadata_json or {},
        processed_at=activity.processed_at,
        created_at=activity.created_at,
        updated_at=activity.updated_at,
    )


def verify_n8n_api_key(x_api_key: str | None = Header(default=None)) -> None:
    if not settings.n8n_ingest_api_key:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="n8n ingestion is not configured")
    if not x_api_key or not compare_digest(x_api_key, settings.n8n_ingest_api_key):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")


@router.get("", response_model=list[ActivityResponse])
def list_activities(db: Session = Depends(get_db)):
    activities = db.scalars(select(Activity).order_by(Activity.event_created_at.desc().nullslast(), Activity.id.desc())).all()
    return [serialize_activity(activity) for activity in activities]


@router.post("", response_model=ActivityResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(verify_n8n_api_key)])
def ingest_activity(payload: ActivityCreate, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == settings.default_user_email))
    if user is None:
        user = User(email=settings.default_user_email, display_name="n8n")
        db.add(user)
        db.flush()

    activity = db.scalar(
        select(Activity).where(
            Activity.user_id == user.id,
            Activity.source == payload.source,
            Activity.external_id == payload.external_id,
        )
    )
    values = payload.model_dump()
    values["metadata_json"] = values.pop("metadata")
    values["processed_at"] = datetime.now(timezone.utc)

    if activity is None:
        activity = Activity(user_id=user.id, **values)
        db.add(activity)
    else:
        for field, value in values.items():
            setattr(activity, field, value)

    db.commit()
    db.refresh(activity)
    return serialize_activity(activity)
