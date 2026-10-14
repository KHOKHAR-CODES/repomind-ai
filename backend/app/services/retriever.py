
from functools import lru_cache

from .embeddings import EmbeddingService
from .vector_store import VectorStore


@lru_cache(maxsize=1)
def get_embedder():
    return EmbeddingService()


@lru_cache(maxsize=1)
def get_vector_store():
    return VectorStore()


class Retriever:
    def __init__(self):
        self.embedder = get_embedder()
        self.store = get_vector_store()

    def retrieve(
        self,
        question: str,
        user_id: int,
        repo_id: int,
        top_k: int = 5,
    ):
        embedding = self.embedder.embed([question])[0]

        return self.store.query_chunks(
            embedding,
            user_id,
            repo_id,
            top_k=min(max(top_k, 1), 10),
        )
