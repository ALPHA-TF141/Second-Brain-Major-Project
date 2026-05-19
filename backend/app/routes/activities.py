from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database.session import get_db
from app.models.activity import Activity
from app.models.timeline_event import TimelineEvent
from app.models.user import User
from app.schemas.activity import ActivityCreate, ActivityOut


router = APIRouter()


@router.post("", response_model=ActivityOut)
def save_activity(payload: ActivityCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    activity = Activity(user_id=user.id, **payload.model_dump())
    db.add(activity)
    db.add(
        TimelineEvent(
            user_id=user.id,
            title=payload.title,
            description=payload.description,
            event_type=payload.activity_type,
        )
    )
    db.commit()
    db.refresh(activity)
    return activity


@router.get("", response_model=list[ActivityOut])
def list_activities(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return (
        db.query(Activity)
        .filter(Activity.user_id == user.id)
        .order_by(Activity.created_at.desc())
        .limit(50)
        .all()
    )
