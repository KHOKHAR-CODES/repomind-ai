import logging
import shutil
from pathlib import Path
from urllib.parse import urlsplit

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.dependencies import get_current_user
from app.models import Repository, User
from app.schemas.repository import RepositoryCreate, RepositoryOut
from app.services.github_service import GitHubService, GitHubServiceError
from app.services.repository_processor import RepositoryProcessor

router = APIRouter(prefix="/api/repositories", tags=["repositories"])
logger = logging.getLogger(__name__)


def _canonical_url(url: str) -> str:
    parts = urlsplit(url.strip()).path.strip("/").split("/")
    name = parts[1].removesuffix(".git")
    return f"https://github.com/{parts[0].lower()}/{name.lower()}"


def _checkout_path(user_id: int, url: str) -> Path:
    parts = urlsplit(url.strip()).path.strip("/").split("/")
    owner, name = parts[0], parts[1].removesuffix(".git")
    return (Path(settings.REPOS_PATH).expanduser().resolve() / str(user_id) / owner / name).resolve()


def _index(repo: Repository, db: Session, user_id: int, force_refresh: bool = False) -> Repository:
    repo.indexing_status = "indexing"
    db.commit()
    db.refresh(repo)
    try:
        local_path = _checkout_path(user_id, repo.repo_url)
        repo.local_path = str(local_path)
        db.commit()
        GitHubService.clone_or_pull(repo.repo_url, str(local_path), repo.branch or "main")
        # Reindexing upserts new chunks first and prunes stale IDs only after success.
        processor = RepositoryProcessor()
        chunk_count = processor.process(str(local_path), user_id, repo.id, repo.repo_name, repo.repo_url)
        repo.file_count = processor.file_count
        repo.chunk_count = chunk_count
        repo.indexing_status = "completed"
        db.commit()
        db.refresh(repo)
        return repo
    except Exception:
        db.rollback()
        current = db.query(Repository).filter(Repository.id == repo.id, Repository.user_id == user_id).first()
        if current:
            current.indexing_status = "failed"
            db.commit()
        logger.exception("Repository indexing failed (user_id=%s, repository_id=%s)", user_id, repo.id)
        raise HTTPException(status_code=502, detail="Repository clone or indexing failed. Check backend logs and verify the public GitHub URL, branch, and indexing dependencies.") from None


@router.post("", response_model=RepositoryOut)
def create_repo(payload: RepositoryCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if not GitHubService.is_valid_github_url(payload.repo_url):
        raise HTTPException(status_code=400, detail="Use an HTTPS GitHub URL in the form https://github.com/owner/repository")
    branch = payload.branch or "main"
    if not GitHubService.validate_branch(branch):
        raise HTTPException(status_code=400, detail="Invalid repository branch name")
    normalized = _canonical_url(payload.repo_url)
    existing = db.query(Repository).filter(Repository.user_id == user.id).all()
    repo = next((item for item in existing if _canonical_url(item.repo_url) == normalized), None)
    if repo:
        if not payload.force_reindex:
            raise HTTPException(status_code=409, detail="This repository is already connected. Use its reindex action to refresh it.")
        repo.branch = branch
        return _index(repo, db, user.id, force_refresh=True)
    parts = urlsplit(payload.repo_url.strip()).path.strip("/").split("/")
    name = parts[1].removesuffix(".git")
    repo = Repository(user_id=user.id, repo_name=name, repo_url=f"https://github.com/{parts[0]}/{name}", branch=branch, indexing_status="pending")
    db.add(repo)
    db.commit()
    db.refresh(repo)
    return _index(repo, db, user.id)


@router.get("", response_model=list[RepositoryOut])
def list_repos(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(Repository).filter(Repository.user_id == user.id).order_by(Repository.id.desc()).all()


@router.get("/{repo_id}", response_model=RepositoryOut)
def get_repo(repo_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    repo = db.query(Repository).filter(Repository.id == repo_id, Repository.user_id == user.id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    return repo


@router.post("/{repo_id}/reindex", response_model=RepositoryOut)
def reindex(repo_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    repo = db.query(Repository).filter(Repository.id == repo_id, Repository.user_id == user.id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    return _index(repo, db, user.id, force_refresh=True)


@router.delete("/{repo_id}")
def delete_repo(repo_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    repo = db.query(Repository).filter(Repository.id == repo_id, Repository.user_id == user.id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    expected = _checkout_path(user.id, repo.repo_url)
    actual = Path(repo.local_path).resolve() if repo.local_path else None
    db.delete(repo)
    db.commit()
    if actual == expected and actual.exists():
        try:
            shutil.rmtree(actual)
        except OSError:
            logger.warning("Could not remove repository checkout (repository_id=%s)", repo_id)
    try:
        from app.services.vector_store import VectorStore
        VectorStore().delete_repo(user.id, repo_id)
    except Exception:
        logger.warning("Could not remove repository vectors (repository_id=%s)", repo_id, exc_info=True)
    return {"message": "Deleted"}
