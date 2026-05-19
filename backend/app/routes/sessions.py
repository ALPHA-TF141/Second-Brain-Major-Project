from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database.session import get_db
from app.models.session import UserSession
from app.models.user import User
from app.schemas.session import SessionCreate, SessionOut
from app.services.auth_service import create_login_session


router = APIRouter()


@router.post("", response_model=SessionOut)
def create_session(payload: SessionCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _token, session = create_login_session(db, user, payload.device_name)
    return session


@router.get("", response_model=list[SessionOut])
def list_sessions(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return (
        db.query(UserSession)
        .filter(UserSession.user_id == user.id)
        .order_by(UserSession.created_at.desc())
        .limit(20)
        .all()
    )
