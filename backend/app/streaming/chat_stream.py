from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.auth.security import decode_token
from app.database.session import SessionLocal
from app.models.user import User
from app.rag.pipeline import rag_pipeline


router = APIRouter()


@router.websocket("/ws/chat")
async def chat_stream(websocket: WebSocket):
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
    try:
        await websocket.send_json({"type": "status", "status": "connected"})
        while True:
            data = await websocket.receive_json()
            question = data.get("question", "").strip()
            if not question:
                await websocket.send_json({"type": "error", "message": "Question is required"})
                continue

            async for event in rag_pipeline.answer_stream(
                db,
                user.id,
                question,
                data.get("conversation_id"),
                data.get("mode", "summary"),
            ):
                await websocket.send_json(event)
    except WebSocketDisconnect:
        pass
    finally:
        db.close()
