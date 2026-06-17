import os
import requests
from datetime import datetime, timedelta
from .models import Repo

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
BASE_URL = "https://api.github.com/search/repositories"


def fetch_github_repos(limit=50) -> list[Repo]:
    print("[GitHub] Fetching trending repos...")
    two_weeks_ago = (datetime.utcnow() - timedelta(days=14)).strftime("%Y-%m-%d")

    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "trend-intel/1.0",
    }
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"

    params = {
        "q": f"pushed:>{two_weeks_ago} stars:>500",
        "sort": "stars",
        "order": "desc",
        "per_page": limit,
    }

    try:
        res = requests.get(BASE_URL, headers=headers, params=params, timeout=15)
        res.raise_for_status()
        repos = []
        for r in res.json().get("items", []):
            repos.append(
                Repo(
                    name=r["full_name"].lower(),
                    url=r["html_url"],
                    description=r.get("description"),
                    language=r.get("language"),
                    stars=r["stargazers_count"],
                    forks=r["forks_count"],
                    source="github",
                )
            )
        print(f"[GitHub] Fetched {len(repos)} repos.")
        return repos
    except requests.exceptions.RequestException as e:
        print(f"[GitHub] Error: {e}")
        return []
