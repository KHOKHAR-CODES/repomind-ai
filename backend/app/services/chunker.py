"""Character-recursive source chunking with line-number preservation."""
from __future__ import annotations
from functools import lru_cache
from typing import Any

DEFAULT_CHUNK_SIZE = 1200
DEFAULT_CHUNK_OVERLAP = 150
SEPARATORS = [
    "\nclass ", "\nasync def ", "\ndef ", "\nfunction ", "\nexport ",
    "\n\n", "\n", ";", " ", "",
]
try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:  # The dependency is declared; this fallback keeps basic indexing usable without it.
    RecursiveCharacterTextSplitter = None

@lru_cache(maxsize=8)
def _splitter(chunk_size: int, overlap: int) -> Any:
    if RecursiveCharacterTextSplitter is None:
        return None
    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        separators=SEPARATORS,
        add_start_index=True,
        strip_whitespace=True,
        length_function=len,
    )

def is_blank(text: str) -> bool:
    return not text or not text.strip()

def _fallback_split(text: str, chunk_size: int, overlap: int) -> list[tuple[str, int]]:
    """Dependency-free recursive-boundary fallback; prefers code/paragraph boundaries."""
    output: list[tuple[str, int]] = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        if end < len(text):
            lower = min(end, start + max(1, chunk_size // 2))
            for separator in SEPARATORS:
                if not separator:
                    continue
                boundary = text.rfind(separator, lower, end)
                if boundary >= lower:
                    end = boundary + len(separator)
                    break
        raw = text[start:end]
        chunk = raw.strip()
        if chunk:
            found = text.find(chunk, start, end)
            output.append((chunk, found if found >= 0 else start))
        if end >= len(text):
            break
        start = max(start + 1, end - overlap)
    return output

def chunk_text(
    text: str,
    file_path: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[dict[str, Any]]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be non-negative and smaller than chunk_size")
    if is_blank(text):
        return []
    pieces: list[tuple[str, int]] = []
    splitter = _splitter(chunk_size, overlap)
    if splitter is not None:
        try:
            documents = splitter.create_documents([text], metadatas=[{"file_path": file_path}])
            cursor = 0
            for document in documents:
                content = str(document.page_content).strip()
                if not content:
                    continue
                raw_start = document.metadata.get("start_index")
                if not isinstance(raw_start, int) or raw_start < 0:
                    raw_start = text.find(content, cursor)
                if raw_start < 0:
                    raw_start = cursor
                pieces.append((content, raw_start))
                cursor = max(cursor, raw_start + max(1, len(content) - overlap))
        except Exception:
            # Source syntax is never parsed; if the splitter library fails on malformed text,
            # fall back to safe character boundaries instead of aborting the repository.
            pieces = _fallback_split(text, chunk_size, overlap)
    else:
        pieces = _fallback_split(text, chunk_size, overlap)
    chunks = []
    for i, (content, start_offset) in enumerate(pieces):
        start_line = text.count("\n", 0, start_offset) + 1
        last_char = max(start_offset, min(len(text) - 1, start_offset + len(content.rstrip("\n")) - 1))
        end_line = max(start_line, text.count("\n", 0, last_char) + 1)
        chunks.append({
            "content": content,
            "start_line": start_line,
            "end_line": end_line,
            "file_path": file_path,
            "chunk_index": i,
        })
    return chunks
