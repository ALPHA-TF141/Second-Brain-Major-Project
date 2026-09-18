import asyncio
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.audio_streaming.voice_stream import router as voice_stream_router
from app.config import settings
from app.database.init_db import init_database
from app.routes import activities, auth, capture, chat, graph, health, memory, ocr, semantic, sessions, settings as settings_routes, social, timeline, voice
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
app.include_router(social.router)
app.include_router(websocket_router)
app.include_router(chat_stream_router)
app.include_router(voice_stream_router)

# Mount Memory Vault for static inspection of cards and hero images
if not os.path.exists("memory_vault"):
    os.makedirs("memory_vault", exist_ok=True)
app.mount("/vault", StaticFiles(directory="memory_vault"), name="vault")


@app.on_event("startup")
async def on_startup():
    init_database()
    initialize_neo4j()
    ocr_processor.start_worker()
    embedding_worker.start()

    # Launch periodic GitHub Memory Vault sync (every 60s background guarantee)
    async def _vault_sync_loop():
        from app.agents.vault_agent import vault_agent
        while True:
            await asyncio.sleep(60)
            try:
                await vault_agent.sync_to_github()
            except Exception:
                pass

    asyncio.create_task(_vault_sync_loop())
