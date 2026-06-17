import os
import requests
from datetime import datetime, timedelta
from .models import Repo

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
BASE_URL = "https://api.github.com/search/repositories"
REPO_URL = "https://api.github.com/repos/{}"


def _headers() -> dict:
    h = {"Accept": "application/vnd.github+json", "User-Agent": "trend-intel/1.0"}
    if GITHUB_TOKEN:
        h["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    return h


def normalize_url(url: str) -> str:
    """Lowercase, strip trailing slash, query string and fragment."""
    url = (url or "").strip().lower()
    url = url.split("?")[0].split("#")[0].rstrip("/")
    return url


def fetch_single_repo(slug: str) -> Repo | None:
    """Fetch metadata for a single repo by owner/repo slug from GitHub API."""
    try:
        res = requests.get(REPO_URL.format(slug), headers=_headers(), timeout=10)
        if res.status_code == 404:
            return None
        res.raise_for_status()
        r = res.json()
        return Repo(
            name=r["full_name"].lower(),
            url=normalize_url(r["html_url"]),
            description=r.get("description"),
            language=r.get("language"),
            stars=r["stargazers_count"],
            forks=r["forks_count"],
            source="github",
        )
    except requests.exceptions.RequestException:
        return None


def fetch_github_repos(limit=50) -> list[Repo]:
    print("[GitHub] Fetching trending repos...")
    two_weeks_ago = (datetime.utcnow() - timedelta(days=14)).strftime("%Y-%m-%d")

    params = {
        "q": f"pushed:>{two_weeks_ago} stars:>500",
        "sort": "stars",
        "order": "desc",
        "per_page": limit,
    }

    try:
        res = requests.get(BASE_URL, headers=_headers(), params=params, timeout=15)
        res.raise_for_status()
        repos = [
            Repo(
                name=r["full_name"].lower(),
                url=normalize_url(r["html_url"]),
                description=r.get("description"),
                language=r.get("language"),
                stars=r["stargazers_count"],
                forks=r["forks_count"],
                source="github",
            )
            for r in res.json().get("items", [])
        ]
        print(f"[GitHub] Fetched {len(repos)} repos.")
        return repos
    except requests.exceptions.RequestException as e:
        print(f"[GitHub] Error: {e}")
        return []
