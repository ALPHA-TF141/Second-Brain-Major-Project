from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_token_payload
from app.database.session import get_db
from app.schemas.auth import LoginRequest, LogoutResponse, TokenResponse
from app.services.auth_service import authenticate_user, create_login_session, end_session


router = APIRouter()


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = authenticate_user(db, payload.username, payload.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")

    token, _session = create_login_session(db, user, payload.device_name)
    return TokenResponse(access_token=token, username=user.username)


@router.post("/logout", response_model=LogoutResponse)
def logout(token_payload: dict = Depends(get_token_payload), db: Session = Depends(get_db)):
    token_jti = token_payload.get("jti")
    end_session(db, token_jti)
    return LogoutResponse(message="Logged out")
