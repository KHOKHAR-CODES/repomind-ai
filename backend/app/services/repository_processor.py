"""Backward-compatible repository processor delegating to the optimized Indexer."""
from .indexer import Indexer

class RepositoryProcessor:
    def __init__(self, indexer=None):
        self.indexer = indexer or Indexer()
        self.file_count = 0
        self.stats = None

    def process(self, repo_path, user_id, repo_id, repo_name, repo_url, commit_hash="") -> int:
        self.stats = self.indexer.index_repository(
            repo_path=repo_path,
            user_id=user_id,
            repo_id=repo_id,
            repo_name=repo_name,
            repo_url=repo_url,
            commit_hash=commit_hash,
        )
        self.file_count = self.stats.file_count
        return self.stats.chunk_count
