"""Repository RAG indexing: safe scan, 1200/150 chunks, ONNX batches, bulk Chroma."""
from __future__ import annotations
from dataclasses import dataclass
import hashlib
import math
import time
from typing import Any

from .chunker import DEFAULT_CHUNK_OVERLAP, DEFAULT_CHUNK_SIZE, chunk_text
from .embeddings import EmbeddingService
from .repo_loader import MAX_FILE_SIZE_BYTES, scan_repository

DEFAULT_EMBEDDING_BATCH_SIZE = 64
DEFAULT_VECTOR_BATCH_SIZE = 300

def _chunk_ids(metadata_list: list[dict[str, Any]]) -> list[str]:
    # Keep a stable ID scheme using user_id, repository_id, file_path, start_line, and chunk_index.
    return [hashlib.md5((
        str(item.get("user_id", "")) + "_" + str(item.get("repository_id", "")) + "_" +
        str(item.get("file_path", "")) + "_" + str(item.get("start_line", 0)) + "_" +
        str(item.get("chunk_index", 0))
    ).encode("utf-8")).hexdigest() for item in metadata_list]

@dataclass(frozen=True)
class IndexStats:
    file_count: int
    chunk_count: int
    skipped_files: int
    scan_seconds: float
    split_seconds: float
    embedding_seconds: float
    persist_seconds: float

class Indexer:
    def __init__(
        self,
        vector_store=None,
        embedder=None,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
        embedding_batch_size: int = DEFAULT_EMBEDDING_BATCH_SIZE,
        vector_batch_size: int = DEFAULT_VECTOR_BATCH_SIZE,
        max_file_bytes: int = MAX_FILE_SIZE_BYTES,
    ):
        if vector_batch_size <= 0 or embedding_batch_size <= 0:
            raise ValueError("batch sizes must be positive")
        if vector_store is None:
            from .vector_store import VectorStore
            vector_store = VectorStore()
        self.vector_store = vector_store
        self.embedder = embedder or EmbeddingService()
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.embedding_batch_size = embedding_batch_size
        self.vector_batch_size = vector_batch_size
        self.max_file_bytes = max_file_bytes

    @staticmethod
    def _log(message: str) -> None:
        print(f"[index] {message}", flush=True)

    def index_repository(
        self,
        repo_path: str,
        user_id: int,
        repo_id: int,
        repo_name: str,
        repo_url: str,
        commit_hash: str = "",
    ) -> IndexStats:
        stage = time.time()
        scan = scan_repository(repo_path, max_file_bytes=self.max_file_bytes)
        scan_seconds = time.time() - stage
        self._log(f"scan/filter: {scan.file_count} valid text files; {scan.skipped_count} skipped; {scan_seconds:.2f}s")

        stage = time.time()
        chunks: list[dict[str, Any]] = []
        for source in scan.files:
            file_chunks = chunk_text(source.content, source.relative_path, self.chunk_size, self.chunk_overlap)
            for chunk in file_chunks:
                chunk["language"] = source.language
            chunks.extend(file_chunks)
        split_seconds = time.time() - stage
        self._log(f"split: {len(chunks)} chunks at {self.chunk_size}/{self.chunk_overlap}; {split_seconds:.2f}s")

        embedding_seconds = 0.0
        persist_seconds = 0.0
        keep_ids: list[str] = []
        batch_count = math.ceil(len(chunks) / self.vector_batch_size) if chunks else 0
        for batch_number, start in enumerate(range(0, len(chunks), self.vector_batch_size), start=1):
            batch = chunks[start:start + self.vector_batch_size]
            self._log(f"batch {batch_number}/{batch_count}: embedding {len(batch)} chunks (FastEmbed inner batch={self.embedding_batch_size})")
            texts = [chunk["content"] for chunk in batch]
            stage = time.time()
            vectors = self.embedder.embed(texts, batch_size=self.embedding_batch_size)
            embedding_seconds += time.time() - stage
            if len(vectors) != len(batch):
                raise RuntimeError(f"Embedding count mismatch: expected {len(batch)}, received {len(vectors)}")
            metadata = [{
                "user_id": int(user_id),
                "repository_id": int(repo_id),
                "repo_name": str(repo_name),
                "repo_url": str(repo_url),
                "file_path": chunk["file_path"],
                "start_line": int(chunk["start_line"]),
                "end_line": int(chunk["end_line"]),
                "language": chunk.get("language", "text"),
                "commit_hash": str(commit_hash or ""),
            } for chunk in batch]
            stage = time.time()
            result_ids = self.vector_store.add_chunks(batch, vectors, metadata)
            persist_seconds += time.time() - stage
            keep_ids.extend(result_ids if result_ids is not None else _chunk_ids(metadata))

        # Do not destroy a working index before new embeddings persist. Once indexing succeeds,
        # prune obsolete chunks (for removed/shortened files) while retaining stable IDs.
        prune = getattr(self.vector_store, "prune_repo", None)
        if callable(prune):
            stage = time.time()
            prune(int(user_id), int(repo_id), keep_ids)
            persist_seconds += time.time() - stage

        self._log(f"embeddings: {embedding_seconds:.2f}s total")
        self._log(f"Chroma persistence/prune: {persist_seconds:.2f}s total")
        return IndexStats(
            file_count=scan.file_count,
            chunk_count=len(chunks),
            skipped_files=scan.skipped_count,
            scan_seconds=scan_seconds,
            split_seconds=split_seconds,
            embedding_seconds=embedding_seconds,
            persist_seconds=persist_seconds,
        )

def index_local_repository(
    repo_path: str,
    user_id: int,
    repo_id: int,
    repo_name: str,
    repo_url: str,
    commit_hash: str = "",
    *,
    vector_store=None,
    embedder=None,
) -> IndexStats:
    """Convenience function to index an already-cloned local checkout safely."""
    return Indexer(vector_store=vector_store, embedder=embedder).index_repository(
        repo_path, user_id, repo_id, repo_name, repo_url, commit_hash
    )
