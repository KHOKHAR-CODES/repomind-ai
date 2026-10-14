"""Compatibility wrappers for the canonical safe repository loader."""
from pathlib import Path
from app.services.repo_loader import (
    ALLOWED_EXTENSIONS, EXCLUDED_DIRS, LANGUAGE_BY_EXTENSION, MAX_FILE_SIZE_BYTES,
    get_extension, is_allowed_file, iter_candidate_paths, read_text_file,
)
SKIP_DIRS = EXCLUDED_DIRS

def get_language(path: str) -> str:
    return LANGUAGE_BY_EXTENSION.get(get_extension(path), "text")

def should_skip_dir(name: str) -> bool:
    return name.casefold() in {entry.casefold() for entry in EXCLUDED_DIRS}

def is_minified(path: str, content: str) -> bool:
    extension = get_extension(path)
    if extension not in {".js", ".css"}:
        return False
    lines = [line for line in content.splitlines() if line.strip()]
    return bool(lines) and sum(map(len, lines)) / len(lines) > 1000

def iter_candidate_files(root: str):
    for absolute, relative in iter_candidate_paths(root):
        yield str(absolute), relative
