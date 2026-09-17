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
        print("[WS VOICE] Connection rejected: Invalid or missing token")
        await websocket.close(code=1008)
        return

    db = SessionLocal()
    user = db.query(User).filter(User.username == payload.get("sub")).first()
    if not user:
        print("[WS VOICE] Connection rejected: User not found for token")
        db.close()
        await websocket.close(code=1008)
        return

    await websocket.accept()
    print(f"[WS VOICE] Client connected: user_id={user.id} ({user.username})")
    session = None

    try:
        await websocket.send_json({"type": "status", "status": "connected"})
        while True:
            data = await websocket.receive_json()
            event_type = data.get("type")
            print(f"[WS VOICE] Incoming event: {event_type}")

            if event_type == "start":
                session = voice_orchestrator.start_session(db, user.id, data)
                print(f"[WS VOICE] Started voice session id={session.id}")
                await websocket.send_json({
                    "type": "session",
                    "session_id": session.id,
                    "mode": session.mode,
                    "language": session.language,
                })

            elif event_type == "audio" and session:
                audio = voice_orchestrator.store_audio_chunk(db, session.id, data.get("audio", ""))
                await websocket.send_json({"type": "audio_received", "audio_id": audio.id})

            elif event_type == "transcript":
                # Auto-create session if manual transcript sent without pressing Start
                if not session:
                    session = voice_orchestrator.start_session(db, user.id, {"mode": "continuous"})
                    print(f"[WS VOICE] Auto-created voice session id={session.id} for incoming transcript")
                    await websocket.send_json({
                        "type": "session",
                        "session_id": session.id,
                        "mode": session.mode,
                        "language": session.language,
                    })

                text = data.get("text", "").strip()
                if not text:
                    continue

                print(f"[WS VOICE] Processing transcript: '{text}' (final={data.get('final')})")
                await websocket.send_json({"type": "transcript", "speaker": "user", "text": text})

                result = await voice_orchestrator.handle_text(db, user.id, session, text, force=data.get("final", False))
                print(f"[WS VOICE] Intent detected: {result.get('intent')}")
                await websocket.send_json({"type": "intent", "intent": result["intent"]})

                if result["answer"]:
                    print(f"[WS VOICE] Sending answer: {result['answer'][:80]}...")
                    await websocket.send_json({"type": "speaking", "status": "started"})
                    await websocket.send_json(
                        _json_safe({
                            "type": "answer",
                            "text": result["answer"],
                            "references": result["references"],
                            "audio": result["audio"],
                        })
                    )
                    await websocket.send_json({"type": "speaking", "status": "ended"})

            elif event_type == "stop" and session:
                session.status = "ended"
                session.ended_at = datetime.utcnow()
                db.commit()
                print(f"[WS VOICE] Voice session id={session.id} stopped")
                await websocket.send_json({"type": "session_ended", "session_id": session.id})
                session = None

    except WebSocketDisconnect:
        print("[WS VOICE] Client disconnected")
        if session:
            session.status = "ended"
            db.commit()
    except Exception as exc:
        print(f"[WS VOICE ERROR] {exc}")
    finally:
        db.close()
