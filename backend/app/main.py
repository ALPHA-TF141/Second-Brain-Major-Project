import asyncio
import os
import threading
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.audio_streaming.voice_stream import router as voice_stream_router
from app.config import settings
from app.database.init_db import init_database
from app.routes import activities, auth, capture, chat, connectors, google, graph, health, mail, memory, ocr, os_router, proactive, research, semantic, sessions, settings as settings_routes, social, timeline, voice
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
app.include_router(connectors.router)
app.include_router(capture.router, prefix="/api/capture", tags=["capture"])
app.include_router(ocr.router, prefix="/api/ocr", tags=["ocr"])
app.include_router(memory.router, prefix="/api/memory", tags=["memory"])
app.include_router(semantic.router, prefix="/api/semantic", tags=["semantic"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(voice.router, prefix="/api/voice", tags=["voice"])
app.include_router(graph.router, tags=["graph"])
app.include_router(social.router)
app.include_router(os_router.router)
app.include_router(google.router)
app.include_router(mail.router)
app.include_router(proactive.router)
app.include_router(research.router)
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

    # --- Automatic mail ingestion loop ---
    # Reads connected mailboxes on a timer and turns each new email into a
    # memory (SQLite + vault card + wiki + graph). Controlled by
    # MAIL_SYNC_ENABLED / MAIL_SYNC_INTERVAL_MINUTES.
    async def _mail_sync_loop():
        from app.agents.mail_ingestion_agent import mail_ingestion_agent
        from app.auth.dependencies import get_current_user  # noqa: F401  (import guard)
        from app.database.session import SessionLocal
        from app.models.user import User

        # let startup finish before the first pass
        await asyncio.sleep(20)
        while True:
            try:
                if settings.mail_sync_enabled:
                    def run_once():
                        db = SessionLocal()
                        try:
                            owner = db.query(User).order_by(User.id.asc()).first()
                            if owner:
                                return mail_ingestion_agent.sync_all(db, owner.id, notify=True)
                        finally:
                            db.close()
                        return None

                    result = await asyncio.to_thread(run_once)
                    if result and result.get("ingested"):
                        print(f"[MailSync] Ingested {result['ingested']} email(s), "
                              f"{result.get('actions', 0)} action item(s).")
            except Exception as exc:
                print(f"[MailSync] Pass failed: {exc}")
            await asyncio.sleep(max(1, settings.mail_sync_interval_minutes) * 60)

    asyncio.create_task(_mail_sync_loop())

    # --- Hands-free: local wake word + proactive voice ---------------------
    from app.services.wake_service import capture_loop, start_wake_word, wire_proactive_voice

    # Capture THIS loop before any worker thread needs to broadcast into it.
    capture_loop()
    wire_proactive_voice()

    wake_result = start_wake_word()
    if wake_result.get("started"):
        print(f"[Wake] Listening for '{settings.wake_word_model}' "
              f"(threshold {settings.wake_word_threshold}). Say it to summon Jarvis.")
    else:
        print(f"[Wake] Wake word not active: {wake_result.get('reason')}")
        if settings.wake_word_enabled:
            print("[Wake] Alt+J still works. To enable hands-free: "
                  "pip install openwakeword sounddevice")

    if settings.voice_announce_enabled:
        quiet = settings.voice_quiet_hours or "off"
        print(f"[Voice] Proactive announcements on (min priority "
              f"'{settings.voice_announce_min_priority}', quiet hours {quiet}).")

    # --- Google integration status (Gmail + Calendar) ---
    if settings.google_configured:
        from app.integrations.token_store import google_token_store

        try:
            accounts = google_token_store.list_accounts()
            if accounts:
                print(f"[Google] {len(accounts)} account(s) connected: "
                      + ", ".join(a.get("email", "?") for a in accounts))
            else:
                print("[Google] Credentials configured, but no accounts connected yet. "
                      "Open Integrations in the app to link Gmail / Calendar.")
        except Exception as exc:
            print(f"[Google] Token store unavailable: {exc}")
    else:
        print("[Google] Not configured - Gmail and Calendar will show 'Not Connected'. "
              "See GOOGLE_SETUP.md.")


    # ---------------------------------------------------------------------
    # Warm the semantic embedding model in a BACKGROUND thread.
    #
    # Loading sentence-transformers is expensive: the first call downloads the
    # model from HuggingFace and loads ~90MB of weights into memory. That load
    # used to happen INSIDE the first user request, so the first time anything
    # semantic was opened (Semantic Memory, related memories, hybrid search) the
    # request blocked for 30s+ and could exceed the caller's HTTP timeout.
    #
    # Doing it here means the model is usually ready before the UI asks for it.
    # ---------------------------------------------------------------------
    def _warm_embedding_model():
        try:
            from app.embeddings.embedding_model import embedding_model

            if embedding_model.is_ready():
                return
            print("[Semantic] Warming up embedding model in background...")
            model = embedding_model.load()
            if model:
                print("[Semantic] Embedding model ready.")
            else:
                print(f"[Semantic] Embedding model unavailable: {embedding_model.last_error}")
                print("[Semantic] Semantic search will degrade to keyword search.")
        except Exception as exc:  # never let warm-up break startup
            print(f"[Semantic] Warm-up skipped: {exc}")

    threading.Thread(target=_warm_embedding_model, name="embedding-warmup", daemon=True).start()
