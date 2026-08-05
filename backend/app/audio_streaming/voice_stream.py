from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.auth.security import decode_token
from app.database.session import SessionLocal
from app.models.user import User
from app.models.voice import VoiceSession
from app.voice.orchestrator import voice_orchestrator


router = APIRouter()


def _json_safe(value):
    """Convert objects (datetimes, etc.) into JSON-serializable values."""
    if isinstance(value, dict):
        return {k: _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


@router.websocket("/ws/voice")
async def voice_stream(websocket: WebSocket):
    token = websocket.query_params.get("token", "")
    payload = decode_token(token)
    if not payload:
        await websocket.close(code=1008)
        return

    db = SessionLocal()
    user = db.query(User).filter(User.username == payload.get("sub")).first()
    if not user:
        db.close()
        await websocket.close(code=1008)
        return

    await websocket.accept()
    session = None
    try:
        await websocket.send_json({"type": "status", "status": "connected"})
        while True:
            data = await websocket.receive_json()
            event_type = data.get("type")

            if event_type == "start":
                session = voice_orchestrator.start_session(db, user.id, data)
                await websocket.send_json({"type": "session", "session_id": session.id, "mode": session.mode, "language": session.language})

            elif event_type == "audio" and session:
                audio = voice_orchestrator.store_audio_chunk(db, session.id, data.get("audio", ""))
                await websocket.send_json({"type": "audio_received", "audio_id": audio.id})

            elif event_type == "transcript" and session:
                text = data.get("text", "").strip()
                if not text:
                    continue
                await websocket.send_json({"type": "transcript", "speaker": "user", "text": text})
                result = await voice_orchestrator.handle_text(db, user.id, session, text, force=data.get("final", False))
                await websocket.send_json({"type": "intent", "intent": result["intent"]})
                if result["answer"]:
                    await websocket.send_json({"type": "speaking", "status": "started"})
                    await websocket.send_json(_json_safe({
                        "type": "answer",
                        "text": result["answer"],
                        "references": result["references"],
                        "audio": result["audio"],
                    }))
                    await websocket.send_json({"type": "speaking", "status": "ended"})

            elif event_type == "stop" and session:
                session.status = "ended"
                session.ended_at = datetime.utcnow()
                db.commit()
                await websocket.send_json({"type": "session_ended", "session_id": session.id})
                session = None

    except WebSocketDisconnect:
        if session:
            session.status = "ended"
            db.commit()
    finally:
        db.close()