import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import urlsplit


class GitHubServiceError(RuntimeError):
    """A repository URL, branch, or Git operation was invalid or failed."""


class GitHubService:
    @staticmethod
    def is_valid_github_url(url: str) -> bool:
        if not isinstance(url, str) or len(url) > 1024:
            return False
        try:
            parsed = urlsplit(url.strip())
            parts = parsed.path.strip("/").split("/")
            return (
                parsed.scheme == "https"
                and parsed.hostname == "github.com"
                and parsed.port is None
                and not parsed.username
                and not parsed.password
                and not parsed.query
                and not parsed.fragment
                and len(parts) == 2
                and bool(re.fullmatch(r"[A-Za-z0-9_.-]{1,100}", parts[0]))
                and bool(re.fullmatch(r"[A-Za-z0-9_.-]{1,100}(?:\.git)?", parts[1]))
                and parts[0] not in {".", ".."}
                and parts[1].removesuffix(".git") not in {".", ".."}
            )
        except ValueError:
            return False

    @staticmethod
    def validate_branch(branch: str) -> bool:
        return bool(
            isinstance(branch, str)
            and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._/-]{0,254}", branch)
            and ".." not in branch
            and "//" not in branch
            and not branch.endswith("/")
        )

    @classmethod
    def clone_or_pull(cls, url: str, local_path: str, branch: str = "main") -> None:
        if not cls.is_valid_github_url(url):
            raise GitHubServiceError("Only HTTPS URLs for github.com/owner/repository are supported.")
        if not cls.validate_branch(branch):
            raise GitHubServiceError("Invalid repository branch name.")
        destination = Path(local_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        result = None
        staging = None
        try:
            if (destination / ".git").is_dir():
                command = ["git", "-C", str(destination), "pull", "--ff-only", "origin", branch]
                result = subprocess.run(command, capture_output=True, text=True, timeout=300, check=False)
            else:
                if destination.exists():
                    if not destination.is_dir() or any(destination.iterdir()):
                        raise GitHubServiceError("The repository checkout path is not empty.")
                    destination.rmdir()
                staging = Path(tempfile.mkdtemp(prefix=".repo-mind-clone-", dir=destination.parent))
                staging.rmdir()
                command = ["git", "clone", "--depth", "1", "--branch", branch, "--single-branch", url, str(staging)]
                result = subprocess.run(command, capture_output=True, text=True, timeout=600, check=False)
                if result.returncode == 0:
                    staging.replace(destination)
            if result.returncode:
                raise GitHubServiceError("GitHub clone or update failed. Verify that the repository and branch are public and accessible.")
        except subprocess.TimeoutExpired as exc:
            raise GitHubServiceError("The Git operation exceeded its time limit.") from exc
        except OSError as exc:
            raise GitHubServiceError("Git is unavailable on the backend host.") from exc
        finally:
            if staging is not None and staging.exists():
                shutil.rmtree(staging, ignore_errors=True)
