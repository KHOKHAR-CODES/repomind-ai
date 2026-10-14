import json
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies import get_current_user
from app.models import Chat, Message, Repository, User

router = APIRouter(prefix="/api/chats", tags=["chats"])
logger = logging.getLogger(__name__)


class ChatRename(BaseModel):
    title: str = Field(min_length=1, max_length=120)

    @field_validator("title")
    @classmethod
    def strip_title(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Conversation title cannot be empty.")
        return value


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def _owned_chat(db: Session, chat_id: int, user_id: int) -> Chat:
    chat = (
        db.query(Chat)
        .join(Repository, Chat.repository_id == Repository.id)
        .filter(Chat.id == chat_id, Chat.user_id == user_id, Repository.user_id == user_id)
        .first()
    )
    if not chat:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return chat


@router.get("")
def list_chats(
    repository_id: int | None = Query(default=None, gt=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = db.query(Chat, Repository.repo_name).join(Repository, Chat.repository_id == Repository.id)
    query = query.filter(Chat.user_id == user.id, Repository.user_id == user.id)
    if repository_id is not None:
        query = query.filter(Chat.repository_id == repository_id)
    rows = query.order_by(Chat.updated_at.desc(), Chat.id.desc()).limit(100).all()
    return [
        {"id": chat.id, "repository_id": chat.repository_id, "repository_name": repo_name,
         "title": chat.title, "created_at": _iso(chat.created_at), "updated_at": _iso(chat.updated_at)}
        for chat, repo_name in rows
    ]


@router.get("/{chat_id}")
def get_chat(chat_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    chat = _owned_chat(db, chat_id, user.id)
    messages = db.query(Message).filter(Message.chat_id == chat.id).order_by(Message.id.asc()).all()
    output = []
    for message in messages:
        metadata = {}
        if message.source_metadata:
            try:
                metadata = json.loads(message.source_metadata)
            except (TypeError, json.JSONDecodeError):
                logger.warning("Invalid stored chat-source metadata (chat_id=%s)", chat.id)
        output.append({
            "id": message.id, "role": message.role, "content": message.content,
            "created_at": _iso(message.created_at),
            "code_snippets": metadata.get("code_snippets", []),
            "references": metadata.get("references", []), "sources": metadata.get("sources", []),
        })
    return {"id": chat.id, "repository_id": chat.repository_id, "title": chat.title,
            "created_at": _iso(chat.created_at), "updated_at": _iso(chat.updated_at), "messages": output}


@router.patch("/{chat_id}")
def rename_chat(chat_id: int, payload: ChatRename, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    chat = _owned_chat(db, chat_id, user.id)
    chat.title = payload.title
    db.commit()
    db.refresh(chat)
    return {"id": chat.id, "title": chat.title, "updated_at": _iso(chat.updated_at)}


@router.delete("/{chat_id}")
def delete_chat(chat_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    chat = _owned_chat(db, chat_id, user.id)
    db.delete(chat)
    db.commit()
    return {"message": "Conversation deleted"}
