import os
import time
import requests
from datetime import datetime, timedelta
from .models import GitHubRepo

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
BASE_URL = "https://api.github.com/search/repositories"


def fetch_and_stage_github(limit=50):
    """
    Fetches repositories that have been active in the last 14 days,
    sorted by stars to show the most popular active projects.
    """
    print("[GitHub Pipeline] Fetching trending active repositories...")

    # 🚀 The 14-day lookback window
    two_weeks_ago = (datetime.now() - timedelta(days=14)).strftime("%Y-%m-%d")

    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "DeveloperTrendIntelligence",
    }

    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"

    # 🚀 Query: Only active projects (pushed recently) with significant interest (stars)
    params = {
        "q": f"pushed:>{two_weeks_ago} stars:>500",
        "sort": "stars",
        "order": "desc",
        "per_page": limit,
    }

    try:
        response = requests.get(BASE_URL, headers=headers, params=params, timeout=15)
        response.raise_for_status()

        remaining_requests = int(response.headers.get("X-RateLimit-Remaining", 100))
        if remaining_requests < 5:
            print("[GitHub Pipeline] Rate limit low, sleeping for 10 seconds...")
            time.sleep(10)

        repositories = []
        for repo in response.json().get("items", []):
            repositories.append(
                GitHubRepo(
                    technology_id=repo["name"].lower(),
                    repo_name=repo["full_name"],
                    owner=repo["owner"]["login"],
                    language=repo["language"],
                    description=repo["description"],
                    topics=repo.get("topics", []),
                    stars=repo["stargazers_count"],
                    forks=repo["forks_count"],
                    watchers=repo["watchers_count"],
                    open_issues=repo["open_issues_count"],
                    created_at=repo["created_at"],
                    updated_at=repo["updated_at"],
                    pushed_at=repo["pushed_at"],
                    html_url=repo["html_url"],
                    stars_growth_24h=0,
                )
            )

        print(f"Fetched {len(repositories)} active trending repositories.")
        return repositories

    except requests.exceptions.RequestException as e:
        print(f"GitHub API Error: {e}")
        return []