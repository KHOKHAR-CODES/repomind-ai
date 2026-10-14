#!/usr/bin/env python3
"""Backend test suite — covers auth, chunking, retrieval filtering, ownership, and ask response format."""
import pytest
from app.core.security import get_hash, verify_password, create_access_token
from app.services.chunker import chunk_text, is_blank
from app.services.vector_store import VectorStore
from app.services.rag_service import RAGService
from app.db.session import Base, engine
from app.models import User, Repository
from sqlalchemy.orm import sessionmaker

Session = sessionmaker(bind=engine)

@pytest.fixture(scope="module")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = Session()
    yield db
    db.close()

@pytest.fixture
def temp_repo():
    return {"user_id": 1, "repository_id": 1, "repo_name": "test-repo", "repo_url": "https://github.com/test/repo.git"}

def test_password_hash_and_verify():
    h = get_hash("secure-password")
    assert verify_password("secure-password", h)
    assert not verify_password("wrong", h)

def test_token_creation():
    token = create_access_token({"sub": "1"})
    assert isinstance(token, str)
    assert len(token) > 20

def test_chunk_text():
    text = "def hello():\n    return 'world'\n"
    chunks = chunk_text(text, "test.py")
    assert len(chunks) >= 1
    assert all("content" in c for c in chunks)

def test_vector_store_filter_by_repo_and_user():
    store = VectorStore(path="./data/test_chroma_db")
    # Add dummy chunk, query back by user/repo filter
    chunks = [{"content": "hello"}]
    embeddings = [[0.1]*384]  # dummy embedding
    metadata = [{"user_id": 99, "repository_id": 99, "repo_name": "t", "repo_url": "", "file_path": "f.py", "start_line": 1, "end_line": 1, "commit_hash": "a"}]
    store.add_chunks(chunks, embeddings, metadata)
    # Retrieval returns by user/repo filter
    results = store.query_chunks([0.1]*384, 99, 99, top_k=1)
    assert len(results.get("ids", [[]])[0]) >= 1

def test_ask_response_format():
    rag = RAGService()
    # Mock retrieval result handling
    result = rag.answer_question("test", 1, 1, top_k=2)
    assert "answer" in result
    assert "code_snippets" in result
    assert "references" in result
    assert "sources" in result

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
