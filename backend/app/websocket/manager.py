import json
from datetime import date, datetime

from fastapi import WebSocket


def _json_default(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if hasattr(obj, "isoformat"):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_personal_message(self, websocket: WebSocket, message: dict):
        await websocket.send_text(json.dumps(message, default=_json_default))

    async def broadcast(self, message: dict):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message, default=_json_default))
            except (RuntimeError, Exception):
                disconnected.append(connection)

        for connection in disconnected:
            self.disconnect(connection)


manager = ConnectionManager()