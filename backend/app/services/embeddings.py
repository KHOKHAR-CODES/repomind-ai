"""FastEmbed ONNX Runtime CPU embeddings (free/open-source model runtime)."""
from __future__ import annotations
from functools import lru_cache

DEFAULT_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

@lru_cache(maxsize=2)
def _load_model(model_name: str):
    try:
        from fastembed import TextEmbedding
    except ImportError as exc:
        raise RuntimeError("FastEmbed is missing. Install backend requirements with `pip install -r requirements.txt`.") from exc
    return TextEmbedding(model_name=model_name)

class EmbeddingService:
    """Drop-in embed(texts) service backed by FastEmbed's ONNX CPU engine."""
    def __init__(self, model_name: str | None = None):
        if not model_name:
            try:
                from app.core.config import settings
                model_name = settings.EMBEDDING_MODEL
            except Exception:
                model_name = DEFAULT_MODEL_NAME
        self.model_name = model_name or DEFAULT_MODEL_NAME
        self._model = None  # lazy load so scanning starts promptly and model load is timed with embeddings

    @property
    def model(self):
        if self._model is None:
            self._model = _load_model(self.model_name)
        return self._model

    def embed(self, texts: list[str], batch_size: int = 64) -> list[list[float]]:
        if not texts:
            return []
        if batch_size <= 0:
            raise ValueError("batch_size must be positive")
        vectors = self.model.embed(texts, batch_size=batch_size)
        normalized = []
        for vector in vectors:
            values = vector.tolist() if hasattr(vector, "tolist") else list(vector)
            normalized.append([float(value) for value in values])
        return normalized
