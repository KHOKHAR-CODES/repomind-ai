from datetime import datetime

from pydantic import BaseModel


class RepositoryCreate(BaseModel):
    repo_url: str
    branch: str | None = "main"
    force_reindex: bool = False


class RepositoryOut(BaseModel):
    id: int
    repo_name: str
    repo_url: str
    branch: str
    indexing_status: str
    file_count: int
    chunk_count: int
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True
