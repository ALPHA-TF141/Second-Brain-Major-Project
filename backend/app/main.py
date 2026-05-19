from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.audio_streaming.voice_stream import router as voice_stream_router
from app.config import settings
from app.database.init_db import init_database
from app.routes import activities, auth, capture, chat, graph, health, memory, ocr, semantic, sessions, settings as settings_routes, timeline, voice
from app.routes.graph import initialize_neo4j
from app.services.ocr_service import ocr_processor
from app.streaming.chat_stream import router as chat_stream_router
from app.workers.embedding_worker import embedding_worker
from app.websocket.live import router as websocket_router


app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api")
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(sessions.router, prefix="/api/sessions", tags=["sessions"])
app.include_router(activities.router, prefix="/api/activities", tags=["activities"])
app.include_router(timeline.router, prefix="/api/timeline", tags=["timeline"])
app.include_router(settings_routes.router, prefix="/api/settings", tags=["settings"])
app.include_router(capture.router, prefix="/api/capture", tags=["capture"])
app.include_router(ocr.router, prefix="/api/ocr", tags=["ocr"])
app.include_router(memory.router, prefix="/api/memory", tags=["memory"])
app.include_router(semantic.router, prefix="/api/semantic", tags=["semantic"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(voice.router, prefix="/api/voice", tags=["voice"])
app.include_router(graph.router, tags=["graph"])
app.include_router(websocket_router)
app.include_router(chat_stream_router)
app.include_router(voice_stream_router)


@app.on_event("startup")
async def on_startup():
    init_database()
    initialize_neo4j()
    ocr_processor.start_worker()
    embedding_worker.start()
