from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database.session import get_db
from app.models.timeline_event import TimelineEvent
from app.models.user import User
from app.schemas.timeline import TimelineEventCreate, TimelineEventOut


router = APIRouter()


@router.post("", response_model=TimelineEventOut)
def create_timeline_event(
    payload: TimelineEventCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    event = TimelineEvent(user_id=user.id, **payload.model_dump())
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


@router.get("", response_model=list[TimelineEventOut])
def fetch_timeline(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return (
        db.query(TimelineEvent)
        .filter(TimelineEvent.user_id == user.id)
        .order_by(TimelineEvent.created_at.desc())
        .limit(50)
        .all()
    )
