from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.dependencies import get_current_user
from app.models import User, Repository, Chat, Message
from app.schemas.user import UserProfile

router = APIRouter(prefix="/api/users", tags=["users"])

@router.get("/me", response_model=UserProfile)
def get_me(user: User = Depends(get_current_user)):
    return user

@router.get("/stats")
def user_stats(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    repos = db.query(Repository).filter(Repository.user_id == user.id).count()
    files = sum(r.file_count or 0 for r in db.query(Repository).filter(Repository.user_id == user.id).all())
    chunks = sum(r.chunk_count or 0 for r in db.query(Repository).filter(Repository.user_id == user.id).all())
    chats = db.query(Chat).filter(Chat.user_id == user.id).count()
    return {"repositories": repos, "files": files, "chunks": chunks, "chats": chats}
