"""GitHub REST API client for the MCP Gateway."""

from typing import Any, Dict, List

import httpx


GITHUB_API_BASE = "https://api.github.com"
GITHUB_API_VERSION = "2026-03-10"
GITHUB_TIMEOUT = 15.0


class GitHubClientError(Exception):
    """Raised when GitHub API calls fail."""

    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(f"[{code}] {message}")


def _headers() -> Dict[str, str]:
    return {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": GITHUB_API_VERSION,
    }


async def get_user(username: str) -> Dict[str, Any]:
    """Fetch a public GitHub user profile."""

    username = username.strip()

    if not username:
        raise GitHubClientError(
            "INVALID_INPUT",
            "GitHub username cannot be empty",
        )

    url = f"{GITHUB_API_BASE}/users/{username}"

    try:
        async with httpx.AsyncClient(timeout=GITHUB_TIMEOUT) as client:
            response = await client.get(
                url,
                headers=_headers(),
            )
    except httpx.TimeoutException:
        raise GitHubClientError(
            "TIMEOUT",
            "GitHub API request timed out",
        )
    except httpx.RequestError as exc:
        raise GitHubClientError(
            "DEPENDENCY_FAILED",
            f"Unable to connect to GitHub API: {exc}",
        )

    if response.status_code == 404:
        raise GitHubClientError(
            "NOT_FOUND",
            f"GitHub user '{username}' was not found",
        )

    if response.status_code != 200:
        raise GitHubClientError(
            "GITHUB_API_ERROR",
            f"GitHub API returned status {response.status_code}",
        )

    try:
        return response.json()
    except ValueError:
        raise GitHubClientError(
            "INTERNAL_ERROR",
            "GitHub API returned invalid JSON",
        )


async def get_user_repositories(
    username: str,
) -> List[Dict[str, Any]]:
    """Fetch public repositories for a GitHub user."""

    username = username.strip()

    if not username:
        raise GitHubClientError(
            "INVALID_INPUT",
            "GitHub username cannot be empty",
        )

    url = f"{GITHUB_API_BASE}/users/{username}/repos"

    params = {
        "per_page": 100,
        "page": 1,
        "sort": "updated",
    }

    try:
        async with httpx.AsyncClient(timeout=GITHUB_TIMEOUT) as client:
            response = await client.get(
                url,
                headers=_headers(),
                params=params,
            )
    except httpx.TimeoutException:
        raise GitHubClientError(
            "TIMEOUT",
            "GitHub API request timed out",
        )
    except httpx.RequestError as exc:
        raise GitHubClientError(
            "DEPENDENCY_FAILED",
            f"Unable to connect to GitHub API: {exc}",
        )

    if response.status_code == 404:
        raise GitHubClientError(
            "NOT_FOUND",
            f"GitHub user '{username}' was not found",
        )

    if response.status_code != 200:
        raise GitHubClientError(
            "GITHUB_API_ERROR",
            f"GitHub API returned status {response.status_code}",
        )

    try:
        data = response.json()
    except ValueError:
        raise GitHubClientError(
            "INTERNAL_ERROR",
            "GitHub API returned invalid JSON",
        )

    if not isinstance(data, list):
        raise GitHubClientError(
            "INTERNAL_ERROR",
            "GitHub repositories response was not a list",
        )

    return data