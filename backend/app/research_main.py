"""Headless research entrypoint: no screen capture, mail, voice, or connector seeding.

Run: uvicorn app.research_main:app --host 127.0.0.1 --port 8000
Uses the existing database unless DATABASE_URL selects a separate research DB.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database.init_db import Base, engine, SessionLocal
from app.auth.security import hash_password
from app.models.user import User
from app.routes import auth, memory, research, observatory


@asynccontextmanager
async def lifespan(app):
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        if not db.query(User).filter(User.username == settings.demo_username).first():
            db.add(User(username=settings.demo_username, password_hash=hash_password(settings.demo_password)))
            db.commit()
    yield


app = FastAPI(title='SecondBrain Research Workspace', lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origin_list,
                   allow_credentials=True, allow_methods=['*'], allow_headers=['*'])
app.include_router(auth.router, prefix='/api/auth')
app.include_router(memory.router, prefix='/api/memory')
app.include_router(research.router)
app.include_router(observatory.router)


@app.get('/api/health')
def health():
    return {'status': 'ok', 'profile': 'research', 'capture': False,
            'mail_sync': False, 'voice': False}
