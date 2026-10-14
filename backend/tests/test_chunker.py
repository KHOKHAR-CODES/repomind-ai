
import os
import re
from typing import Dict, List


SKIP_DIRS = {
    ".git", "node_modules", "venv", ".venv", "__pycache__",
    "build", "dist", "coverage", ".next", ".cache", ".idea",
    ".vscode", "vendor", "target", "bin", "obj",
}

ALLOWED_EXT = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".go",
    ".rs", ".c", ".cpp", ".h", ".hpp", ".cs", ".php",
    ".rb", ".swift", ".kt", ".md", ".txt", ".json",
    ".yaml", ".yml", ".toml", ".ini", ".env.example",
    ".html", ".css", ".scss",
}


def is_blank(text: str) -> bool:
    """Return True when text is empty or whitespace-only."""
    return not text or not text.strip()


def is_heading(line: str) -> bool:
    """Detect Markdown headings."""
    return bool(
        re.match(r"^\s{0,3}#{1,6}(?:\s+|$)", line)
    )


def is_code_boundary(line: str) -> bool:
    """Detect common function, class, and control-flow boundaries."""
    stripped = line.strip()

    if not stripped:
        return False

    patterns = [
        r"^(?:async\s+)?def\s+\w+\s*\(",
        r"^(?:async\s+)?function\b",
        r"^(?:export\s+)?class\s+\w+\b",
        r"^(?:if|elif|else|for|while|try|except|finally|with)\b.*:",
    ]

    return any(re.match(pattern, stripped) for pattern in patterns)


def chunk_text(
    text: str,
    file_path: str,
    chunk_size: int = 1000,
    overlap: int = 150,
) -> List[Dict]:
    """
    Split text into overlapping chunks while preserving source line numbers.

    Chunk boundaries are selected at line boundaries. The overlap is
    approximately the requested number of characters, adjusted to retain
    complete lines where possible.
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero")

    if overlap < 0:
        raise ValueError("overlap cannot be negative")

    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    if not text or not text.strip():
        return []

    lines = text.splitlines()
    chunks: List[Dict] = []

    start_index = 0
    total_lines = len(lines)

    while start_index < total_lines:
        end_index = start_index
        current_length = 0

        # Include complete lines until the chunk reaches its target size.
        while end_index < total_lines:
            line_length = len(lines[end_index]) + 1

            if end_index > start_index and (
                current_length + line_length > chunk_size
            ):
                break

            current_length += line_length
            end_index += 1

            if current_length >= chunk_size:
                break

        chunk_content = "\n".join(lines[start_index:end_index])

        if chunk_content.strip():
            chunks.append(
                {
                    "content": chunk_content,
                    "start_line": start_index + 1,
                    "end_line": end_index,
                    "file_path": file_path,
                }
            )

        if end_index >= total_lines:
            break

        # Move backwards from the next chunk boundary to retain overlap.
        next_start = end_index
        overlap_length = 0

        while next_start > start_index and overlap_length < overlap:
            next_start -= 1
            overlap_length += len(lines[next_start]) + 1

        # Always advance at least one line to avoid an infinite loop.
        start_index = max(start_index + 1, next_start)

    return chunks
