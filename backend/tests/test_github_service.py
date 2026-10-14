import pytest

from app.services.github_service import GitHubService


@pytest.mark.parametrize(
    "url",
    [
        "https://github.com/owner/repository",
        "https://github.com/owner/repository.git",
    ],
)
def test_accepts_supported_github_urls(url):
    assert GitHubService.is_valid_github_url(url)


@pytest.mark.parametrize(
    "url",
    [
        "http://github.com/owner/repository",
        "https://github.com.evil.example/owner/repository",
        "https://attacker@example.com/owner/repository",
        "https://github.com/owner/repository?token=secret",
        "https://github.com/owner/repository/tree/main",
        "git@github.com:owner/repository.git",
    ],
)
def test_rejects_unsupported_or_ambiguous_urls(url):
    assert not GitHubService.is_valid_github_url(url)


@pytest.mark.parametrize("branch", ["main", "release/2026.10", "feature/search-v2"])
def test_accepts_branch_names(branch):
    assert GitHubService.validate_branch(branch)


@pytest.mark.parametrize("branch", ["-upload-pack=evil", "../secret", "feature//name", "main/", ""])
def test_rejects_unsafe_branch_names(branch):
    assert not GitHubService.validate_branch(branch)
