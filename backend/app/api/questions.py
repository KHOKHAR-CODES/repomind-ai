from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies import get_current_user
from app.models import Repository, User
from app.schemas.question import AskRequest, AskResponse
from app.services.chat_service import ChatService
from app.services.llm_service import LLMServiceError

router = APIRouter(prefix="/api/repositories", tags=["questions"])


@router.post("/{repo_id}/ask", response_model=AskResponse)
def ask_question(
    repo_id: int,
    payload: AskRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    repo = db.query(Repository).filter(Repository.id == repo_id, Repository.user_id == user.id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    if repo.indexing_status != "completed":
        raise HTTPException(status_code=400, detail="Repository is not indexed")
    try:
        return ChatService().ask(
            db, user.id, repo_id, payload.question,
            chat_id=payload.chat_id, top_k=payload.top_k,
        )
    except ValueError as exc:
        # Do not disclose whether another account owns the chat or repository.
        raise HTTPException(status_code=404, detail="Conversation or repository not found") from exc
    except LLMServiceError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from None
