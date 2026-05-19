from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.auth.security import decode_token
from app.websocket.manager import manager


router = APIRouter()


@router.websocket("/ws/live")
async def live_updates(websocket: WebSocket):
    token = websocket.query_params.get("token", "")
    payload = decode_token(token)

    if not payload:
        await websocket.close(code=1008)
        return

    await manager.connect(websocket)
    username = payload.get("sub", "user")

    try:
        await manager.send_personal_message(
            websocket,
            {
                "type": "status",
                "status": "connected",
                "message": f"Live connection ready for {username}",
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

        while True:
            data = await websocket.receive_json()
            await manager.send_personal_message(
                websocket,
                {
                    "type": "echo",
                    "status": "ok",
                    "message": data.get("message", "Message received"),
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )
    except WebSocketDisconnect:
        manager.disconnect(websocket)
