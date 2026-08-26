"""Fetches Kevin's public, non-fork GitHub repos live from the REST API at question-time -- no offline snapshot, no ingestion step, no stale file."""

import requests

from app.config import GITHUB_MAX_REPOS, GITHUB_TOKEN, GITHUB_USERNAME

GITHUB_API_BASE = "https://api.github.com"
REQUEST_TIMEOUT_SECONDS = 15


class GitHubFetchError(Exception):
    pass


def _headers() -> dict:
    headers = {"Accept": "application/vnd.github+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    return headers


def fetch_public_repos(username: str = GITHUB_USERNAME, max_repos: int = GITHUB_MAX_REPOS) -> list[dict]:
    url = f"{GITHUB_API_BASE}/users/{username}/repos"
    params = {"sort": "pushed", "direction": "desc", "per_page": max_repos, "type": "owner"}
    try:
        response = requests.get(url, headers=_headers(), params=params, timeout=REQUEST_TIMEOUT_SECONDS)
    except requests.RequestException as error:
        raise GitHubFetchError(f"Network error reaching GitHub API: {error}") from error

    if response.status_code == 404:
        raise GitHubFetchError(f"GitHub user '{username}' not found.")
    if response.status_code == 403:
        raise GitHubFetchError("GitHub API rate-limited this request. Set GITHUB_TOKEN in .env to raise the limit.")
    if response.status_code != 200:
        raise GitHubFetchError(f"GitHub API returned HTTP {response.status_code}: {response.text[:200]}")

    repos = response.json()
    return [repo for repo in repos if not repo.get("fork")]


def _format_repo_excerpt(repo: dict) -> str:
    name = repo.get("name", "unknown")
    description = repo.get("description") or "No description provided."
    language = repo.get("language") or "Not specified"
    topics = repo.get("topics") or []
    topics_line = ", ".join(topics) if topics else "None"
    stars = repo.get("stargazers_count", 0)
    updated = (repo.get("pushed_at") or "")[:10]
    url = repo.get("html_url", "")

    lines = [
        f"GitHub Project: {name}",
        "",
        f"URL: {url}",
        f"Primary language: {language}",
        f"Topics: {topics_line}",
        f"Stars: {stars}",
        f"Last pushed: {updated}",
        "",
        description,
    ]
    return "\n".join(lines)


def fetch_github_excerpts(username: str = GITHUB_USERNAME) -> list[tuple[str, str]]:
    """Returns one (section_title, excerpt_text) pair per real public repo, fetched live right now. Raises GitHubFetchError on network/API failure -- callers decide the fallback."""
    repos = fetch_public_repos(username)
    return [(f"GitHub Project: {repo.get('name', 'unknown')}", _format_repo_excerpt(repo)) for repo in repos]
