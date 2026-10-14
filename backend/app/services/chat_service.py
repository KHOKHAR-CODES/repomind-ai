import json
from sqlalchemy.orm import Session
from app.models import Chat, Message, Repository
from app.services.rag_service import RAGService

class ChatService:
    def __init__(self):
        self.rag = RAGService()

    def ask(self, db: Session, user_id: int, repository_id: int, question: str, chat_id: int | None = None, top_k: int = 5):
        repo = db.query(Repository).filter(Repository.id == repository_id, Repository.user_id == user_id).first()
        if not repo:
            raise ValueError("Repository not found")
        if repo.indexing_status != "completed":
            raise ValueError("Repository is not indexed yet")

        if chat_id:
            chat = db.query(Chat).filter(Chat.id == chat_id, Chat.user_id == user_id, Chat.repository_id == repository_id).first()
            if not chat:
                raise ValueError("Chat not found")
        else:
            chat = Chat(user_id=user_id, repository_id=repository_id, title=question[:80])
            db.add(chat)
            db.commit()
            db.refresh(chat)

        user_msg = Message(chat_id=chat.id, role="user", content=question)
        db.add(user_msg)

        result = self.rag.answer_question(question, user_id, repository_id, top_k=top_k)
        assistant_msg = Message(chat_id=chat.id, role="assistant", content=result["answer"], source_metadata=json.dumps({
            "code_snippets": result["code_snippets"], "references": result["references"], "sources": result["sources"]
        }))
        db.add(assistant_msg)
        db.commit()

        return {
            "chat_id": chat.id,
            "question": question,
            "answer": result["answer"],
            "code_snippets": result["code_snippets"],
            "references": result["references"],
            "sources": result["sources"],
        }
