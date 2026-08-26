import pytest

import app.github_live as gh


class FakeResponse:
    def __init__(self, status_code, payload=None, text=""):
        self.status_code = status_code
        self._payload = payload
        self.text = text

    def json(self):
        return self._payload


def test_fetch_public_repos_filters_out_forks(monkeypatch):
    repos = [
        {"name": "real-project", "fork": False},
        {"name": "forked-project", "fork": True},
    ]
    monkeypatch.setattr(gh.requests, "get", lambda *a, **k: FakeResponse(200, repos))
    result = gh.fetch_public_repos("someuser")
    assert len(result) == 1
    assert result[0]["name"] == "real-project"


def test_fetch_public_repos_raises_on_404(monkeypatch):
    monkeypatch.setattr(gh.requests, "get", lambda *a, **k: FakeResponse(404, text="Not Found"))
    with pytest.raises(gh.GitHubFetchError):
        gh.fetch_public_repos("ghost-user")


def test_fetch_public_repos_raises_on_rate_limit(monkeypatch):
    monkeypatch.setattr(gh.requests, "get", lambda *a, **k: FakeResponse(403, text="rate limited"))
    with pytest.raises(gh.GitHubFetchError, match="rate-limited"):
        gh.fetch_public_repos("someuser")


def test_fetch_public_repos_raises_on_network_error(monkeypatch):
    def boom(*a, **k):
        raise gh.requests.RequestException("connection refused")

    monkeypatch.setattr(gh.requests, "get", boom)
    with pytest.raises(gh.GitHubFetchError, match="Network error"):
        gh.fetch_public_repos("someuser")


def test_fetch_github_excerpts_returns_one_pair_per_repo(monkeypatch):
    repos = [
        {
            "name": "askkevin",
            "description": "A grounded career assistant.",
            "language": "Python",
            "topics": ["ai", "fastapi"],
            "stargazers_count": 3,
            "pushed_at": "2026-01-15T00:00:00Z",
            "html_url": "https://github.com/kevintlee01/askkevin",
            "fork": False,
        }
    ]
    monkeypatch.setattr(gh.requests, "get", lambda *a, **k: FakeResponse(200, repos))
    excerpts = gh.fetch_github_excerpts("kevintlee01")
    assert len(excerpts) == 1
    section, text = excerpts[0]
    assert section == "GitHub Project: askkevin"
    assert "A grounded career assistant." in text
    assert "Python" in text
    assert "ai, fastapi" in text
    assert "https://github.com/kevintlee01/askkevin" in text


def test_fetch_github_excerpts_propagates_fetch_errors(monkeypatch):
    monkeypatch.setattr(gh.requests, "get", lambda *a, **k: FakeResponse(404, text="Not Found"))
    with pytest.raises(gh.GitHubFetchError):
        gh.fetch_github_excerpts("ghost-user")
