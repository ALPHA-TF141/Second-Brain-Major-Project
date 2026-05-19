from datetime import datetime

from sqlalchemy.orm import Session

from app.auth.security import create_access_token, verify_password
from app.models.session import UserSession
from app.models.user import User


def authenticate_user(db: Session, username: str, password: str) -> User | None:
    user = db.query(User).filter(User.username == username, User.is_active == True).first()
    if not user or not verify_password(password, user.password_hash):
        return None
    return user


def create_login_session(db: Session, user: User, device_name: str) -> tuple[str, UserSession]:
    token, token_jti = create_access_token(user.username)
    session = UserSession(user_id=user.id, token_jti=token_jti, device_name=device_name)
    db.add(session)
    db.commit()
    db.refresh(session)
    return token, session


def end_session(db: Session, token_jti: str) -> bool:
    session = db.query(UserSession).filter(UserSession.token_jti == token_jti).first()
    if not session:
        return False

    session.is_active = False
    session.ended_at = datetime.utcnow()
    db.commit()
    return True
