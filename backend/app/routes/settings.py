from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database.session import get_db
from app.models.setting import Setting
from app.models.user import User
from app.schemas.setting import SettingOut, SettingUpdate


router = APIRouter()


@router.get("", response_model=list[SettingOut])
def get_settings(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(Setting).filter(Setting.user_id == user.id).order_by(Setting.key.asc()).all()


@router.put("", response_model=SettingOut)
def update_setting(payload: SettingUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    setting = db.query(Setting).filter(Setting.user_id == user.id, Setting.key == payload.key).first()
    if not setting:
        setting = Setting(user_id=user.id, key=payload.key)
        db.add(setting)

    setting.value = payload.value
    db.commit()
    db.refresh(setting)
    return setting
