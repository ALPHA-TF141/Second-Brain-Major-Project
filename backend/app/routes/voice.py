from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.auth.security import decode_token
from app.database.session import get_db
from app.models.voice import ConversationAudio, LanguagePreference, Transcript, VoiceSession
from app.models.user import User
from app.schemas.voice import LanguagePreferenceOut, LanguagePreferenceUpdate, TranscriptOut, VoiceSessionOut, VoiceSessionStart
from app.stt.whisper_engine import whisper_stt
from app.tts.coqui_tts import coqui_tts
from app.voice.orchestrator import voice_orchestrator


router = APIRouter()


@router.get("/status")
def voice_status(_user: User = Depends(get_current_user)):
    return {
        "whisper_ready": whisper_stt.is_ready(),
        "whisper_error": whisper_stt.last_error,
        "tts_ready": coqui_tts.is_ready(),
        "tts_error": coqui_tts.last_error,
        "modes": ["continuous", "push_to_talk", "wake_word"],
        "languages": ["mixed", "en", "ta"],
    }


@router.post("/sessions", response_model=VoiceSessionOut)
def start_voice_session(payload: VoiceSessionStart, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return voice_orchestrator.start_session(db, user.id, payload.model_dump())


@router.post("/sessions/{session_id}/stop", response_model=VoiceSessionOut)
def stop_voice_session(session_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    session = db.query(VoiceSession).filter(VoiceSession.id == session_id, VoiceSession.user_id == user.id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Voice session not found")
    session.status = "ended"
    session.ended_at = datetime.utcnow()
    db.commit()
    db.refresh(session)
    return session


@router.get("/sessions", response_model=list[VoiceSessionOut])
def list_voice_sessions(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(VoiceSession).filter(VoiceSession.user_id == user.id).order_by(VoiceSession.started_at.desc()).limit(30).all()


@router.get("/sessions/{session_id}/transcripts", response_model=list[TranscriptOut])
def list_transcripts(session_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    session = db.query(VoiceSession).filter(VoiceSession.id == session_id, VoiceSession.user_id == user.id).first()
    if not session:
        return []
    return db.query(Transcript).filter(Transcript.voice_session_id == session_id).order_by(Transcript.created_at.asc()).all()


@router.get("/preferences", response_model=LanguagePreferenceOut)
def get_preferences(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return voice_orchestrator.get_preferences(db, user.id)


@router.put("/preferences", response_model=LanguagePreferenceOut)
def update_preferences(payload: LanguagePreferenceUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    prefs = voice_orchestrator.get_preferences(db, user.id)
    for key, value in payload.model_dump().items():
        setattr(prefs, key, value)
    db.commit()
    db.refresh(prefs)
    return prefs


@router.get("/audio/{audio_id}")
def get_voice_audio(audio_id: int, token: str = "", db: Session = Depends(get_db)):
    if not decode_token(token):
        raise HTTPException(status_code=401, detail="Invalid token")
    audio = db.query(ConversationAudio).filter(ConversationAudio.id == audio_id).first()
    if not audio or not audio.file_path:
        raise HTTPException(status_code=404, detail="Audio not found")
    path = Path(audio.file_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Audio file missing")
    return FileResponse(path, media_type="audio/wav")
