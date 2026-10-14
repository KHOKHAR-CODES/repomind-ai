#!/usr/bin/env python3
"""Clone a public GitHub repository and index it into the local Chroma store.

Run from backend/: python scripts/index_github_repo.py https://github.com/owner/repo
The first run downloads the small FastEmbed ONNX model into its local cache.
"""
from __future__ import annotations
import argparse
import os
import re
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from git import Repo
from app.services.indexer import Indexer
from app.services.vector_store import VectorStore
from app.core.config import settings

def validate_github_url(value: str) -> tuple[str, str]:
    parsed = urlsplit(value.strip())
    parts = parsed.path.strip("/").split("/")
    if (parsed.scheme != "https" or parsed.hostname != "github.com" or parsed.username or parsed.password
            or parsed.query or parsed.fragment or len(parts) != 2
            or not re.fullmatch(r"[A-Za-z0-9_.-]+", parts[0])
            or not re.fullmatch(r"[A-Za-z0-9_.-]+(?:\.git)?", parts[1], flags=re.IGNORECASE)):
        raise ValueError("Use a public HTTPS GitHub URL: https://github.com/owner/repository")
    repo_name = parts[1].removesuffix(".git")
    return f"https://github.com/{parts[0]}/{repo_name}.git", repo_name

def validate_branch(value: str) -> str:
    if (not value or value.startswith("-") or not re.fullmatch(r"[A-Za-z0-9._/-]{1,255}", value)
            or ".." in value or "//" in value or value.endswith(("/", ".", ".lock")) or "@{" in value):
        raise ValueError("Invalid Git branch name")
    return value

def clone_and_index(url: str, branch: str = "main", user_id: int = 1, repo_id: int = 1,
                    chroma_path: str | None = None):
    clone_url, repo_name = validate_github_url(url)
    branch = validate_branch(branch)
    store = VectorStore(path=chroma_path) if chroma_path else VectorStore()
    with tempfile.TemporaryDirectory(prefix="repomind-index-") as temp:
        checkout = Path(temp) / "checkout"
        safe_env = os.environ.copy()
        safe_env["GIT_TERMINAL_PROMPT"] = "0"
        print(f"[index] shallow-cloning {clone_url} ({branch})", flush=True)
        repository = Repo.clone_from(
            clone_url, str(checkout), branch=branch, depth=1, single_branch=True, env=safe_env
        )
        return Indexer(vector_store=store).index_repository(
            repo_path=str(checkout),
            user_id=user_id,
            repo_id=repo_id,
            repo_name=repo_name,
            repo_url=clone_url.removesuffix(".git"),
            commit_hash=repository.head.commit.hexsha,
        )

def main() -> int:
    parser = argparse.ArgumentParser(description="Clone and index a public GitHub repository locally")
    parser.add_argument("repo_url")
    parser.add_argument("--branch", default="main")
    parser.add_argument("--user-id", type=int, default=1)
    parser.add_argument("--repo-id", type=int, default=1)
    parser.add_argument("--chroma-path", default=None, help=f"Chroma directory (default: {settings.CHROMA_DB_PATH})")
    args = parser.parse_args()
    try:
        stats = clone_and_index(args.repo_url, args.branch, args.user_id, args.repo_id,
                                args.chroma_path or settings.CHROMA_DB_PATH)
    except Exception as exc:
        print(f"[index] failed: {exc}", file=sys.stderr, flush=True)
        return 1
    print(f"[index] complete: {stats.file_count} files, {stats.chunk_count} chunks; "
          f"scan {stats.scan_seconds:.2f}s, split {stats.split_seconds:.2f}s, "
          f"embed {stats.embedding_seconds:.2f}s, Chroma {stats.persist_seconds:.2f}s", flush=True)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
