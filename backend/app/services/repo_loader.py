"""Safe, deterministic source-file discovery for repository indexing.

Only a small explicit set of source/documentation extensions is decoded. Symlinks,
known generated/dependency trees, binary-looking files and oversized files are skipped.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

EXCLUDED_DIRS = frozenset({
    ".git", "node_modules", "venv", ".venv", "__pycache__", "build", "dist",
    ".next", ".idea", ".vscode",
})
ALLOWED_EXTENSIONS = frozenset({
    ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".c", ".cpp", ".h",
    ".cs", ".go", ".rs", ".php", ".rb", ".html", ".css", ".json",
    ".md", ".txt", ".sql", ".yaml", ".yml",
})
SKIP_FILE_NAMES = frozenset({
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "composer.lock",
    "gemfile.lock", "poetry.lock", "cargo.lock",
})
MAX_FILE_SIZE_BYTES = 2 * 1024 * 1024
_BINARY_SAMPLE_BYTES = 8192
_ALLOWED_CONTROL_BYTES = {7, 8, 9, 10, 12, 13, 27}

LANGUAGE_BY_EXTENSION = {
    ".py": "python", ".js": "javascript", ".ts": "typescript", ".jsx": "javascript",
    ".tsx": "typescript", ".java": "java", ".c": "c", ".cpp": "cpp", ".h": "c",
    ".cs": "csharp", ".go": "go", ".rs": "rust", ".php": "php", ".rb": "ruby",
    ".html": "html", ".css": "css", ".json": "json", ".md": "markdown",
    ".txt": "text", ".sql": "sql", ".yaml": "yaml", ".yml": "yaml",
}

@dataclass(frozen=True)
class RepositoryFile:
    absolute_path: Path
    relative_path: str
    content: str
    language: str
    size_bytes: int

@dataclass
class ScanResult:
    files: list[RepositoryFile] = field(default_factory=list)
    skipped: dict[str, int] = field(default_factory=dict)

    @property
    def file_count(self) -> int:
        return len(self.files)

    @property
    def skipped_count(self) -> int:
        return sum(self.skipped.values())

def get_extension(path: str | Path) -> str:
    return Path(path).suffix.lower()

def is_allowed_file(path: str | Path) -> bool:
    candidate = Path(path)
    return candidate.name.lower() not in SKIP_FILE_NAMES and get_extension(candidate) in ALLOWED_EXTENSIONS

def _looks_binary(sample: bytes) -> bool:
    if not sample:
        return False
    if b"\x00" in sample:
        return True
    controls = sum(byte < 32 and byte not in _ALLOWED_CONTROL_BYTES for byte in sample)
    return controls / len(sample) > 0.02

def read_text_file(path: str | Path, max_file_bytes: int = MAX_FILE_SIZE_BYTES) -> str | None:
    """Read UTF-8 text defensively; return None for unreadable, binary or oversized files."""
    candidate = Path(path)
    try:
        if candidate.is_symlink() or not candidate.is_file():
            return None
        size = candidate.stat().st_size
        if size <= 0 or size > max_file_bytes:
            return None
        with candidate.open("rb") as raw:
            if _looks_binary(raw.read(_BINARY_SAMPLE_BYTES)):
                return None
        # Explicit replacement policy requested: malformed UTF-8 never aborts a repository scan.
        with candidate.open("r", encoding="utf-8", errors="ignore") as stream:
            content = stream.read(max_file_bytes + 1)
        if len(content) > max_file_bytes:
            return None
        if not content.strip() or "\x00" in content:
            return None
        return content
    except (OSError, UnicodeError, ValueError):
        return None

def iter_candidate_paths(root: str | Path) -> Iterator[tuple[Path, str]]:
    """Yield safe, whitelisted paths (without decoding their contents)."""
    base = Path(root).expanduser().resolve(strict=True)
    if not base.is_dir():
        raise NotADirectoryError(str(base))
    excluded = {name.casefold() for name in EXCLUDED_DIRS}
    for directory, dirnames, filenames in os.walk(base, topdown=True, followlinks=False):
        dirnames[:] = [name for name in sorted(dirnames)
                       if name.casefold() not in excluded and not (Path(directory) / name).is_symlink()]
        for filename in sorted(filenames):
            path = Path(directory) / filename
            if path.is_symlink() or not is_allowed_file(path):
                continue
            try:
                relative = path.relative_to(base).as_posix()
            except ValueError:
                continue
            yield path, relative

def scan_repository(root: str | Path, max_file_bytes: int = MAX_FILE_SIZE_BYTES) -> ScanResult:
    """Discover, validate, and read indexable files; bad files are counted and skipped."""
    if max_file_bytes <= 0:
        raise ValueError("max_file_bytes must be positive")
    base = Path(root).expanduser().resolve(strict=True)
    if not base.is_dir():
        raise NotADirectoryError(str(base))
    result = ScanResult()
    excluded = {name.casefold() for name in EXCLUDED_DIRS}
    def on_walk_error(error: OSError) -> None:
        result.skipped["unreadable_directory"] = result.skipped.get("unreadable_directory", 0) + 1
    for directory, dirnames, filenames in os.walk(base, topdown=True, followlinks=False, onerror=on_walk_error):
        kept = []
        for name in sorted(dirnames):
            path = Path(directory) / name
            if name.casefold() in excluded or path.is_symlink():
                result.skipped["excluded_directory"] = result.skipped.get("excluded_directory", 0) + 1
            else:
                kept.append(name)
        dirnames[:] = kept
        for filename in sorted(filenames):
            path = Path(directory) / filename
            if path.is_symlink():
                result.skipped["symlink"] = result.skipped.get("symlink", 0) + 1
                continue
            if not is_allowed_file(path):
                result.skipped["unsupported_or_lockfile"] = result.skipped.get("unsupported_or_lockfile", 0) + 1
                continue
            try:
                size = path.stat().st_size
            except OSError:
                result.skipped["unreadable"] = result.skipped.get("unreadable", 0) + 1
                continue
            if size > max_file_bytes:
                result.skipped["oversized"] = result.skipped.get("oversized", 0) + 1
                continue
            if size == 0:
                result.skipped["empty"] = result.skipped.get("empty", 0) + 1
                continue
            content = read_text_file(path, max_file_bytes=max_file_bytes)
            if content is None:
                result.skipped["binary_or_unreadable"] = result.skipped.get("binary_or_unreadable", 0) + 1
                continue
            relative = path.relative_to(base).as_posix()
            result.files.append(RepositoryFile(
                absolute_path=path,
                relative_path=relative,
                content=content,
                language=LANGUAGE_BY_EXTENSION.get(get_extension(path), "text"),
                size_bytes=size,
            ))
    return result
