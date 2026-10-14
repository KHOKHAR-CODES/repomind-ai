from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import auth, chats, health, questions, repositories, users
from app.core.config import settings
from app.db.session import Base, engine


Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.APP_NAME, version="1.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)

app.include_router(auth.router)
app.include_router(repositories.router)
app.include_router(questions.router)
app.include_router(users.router)
app.include_router(chats.router)
app.include_router(health.router)

# Mount static frontend at root for single-domain deploy
try:
    app.mount("/", StaticFiles(directory="../frontend", html=True), name="static")
except Exception:
    pass


