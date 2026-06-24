import re
import time
import requests
from datetime import datetime, timedelta, timezone
from .models import DevArticle

BASE_URL = "https://dev.to/api/articles"
ARTICLE_URL = "https://dev.to/api/articles/{}"
GITHUB_PATTERN = re.compile(r"github\.com/([a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+)")

BANNED_TAGS = {
    "lifestyle", "career", "productivity", "watercooler", "discuss",
    "motivation", "mentalhealth", "bootcamp", "beginners", "management",
}


def extract_github_slug(text: str) -> str | None:
    match = GITHUB_PATTERN.search(text or "")
    if not match:
        return None
    slug = match.group(1).lower().rstrip(".git")
    if any(slug.startswith(p) for p in ("orgs/", "topics/", "collections/")):
        return None
    return slug


def fetch_devto_articles(limit=100) -> tuple[list[DevArticle], dict[str, list]]:
    print("[DEV.to] Fetching articles...")
    cutoff = datetime.now(tz=timezone.utc) - timedelta(days=7)

    headers = {
        "User-Agent": "trend-intel/1.0",
        "Accept": "application/vnd.forem.api-v1+json",
    }

    try:
        res = requests.get(
            BASE_URL, headers=headers, params={"per_page": limit, "top": 7}, timeout=10
        )
        res.raise_for_status()
        raw = res.json()
    except requests.exceptions.RequestException as e:
        print(f"[DEV.to] Error: {e}")
        return [], {}

    articles = []
    slug_map: dict[str, list] = {}
    seen = set()

    for item in raw:
        devto_id = item["id"]
        if devto_id in seen:
            continue

        tags = [t.lower() for t in item.get("tag_list", [])]
        if any(t in BANNED_TAGS for t in tags):
            continue

        try:
            published_at = datetime.fromisoformat(
                item["published_at"].replace("Z", "+00:00")
            )
        except Exception:
            published_at = datetime.now(tz=timezone.utc)

        if published_at < cutoff.replace(tzinfo=timezone.utc):
            continue

        seen.add(devto_id)

        # Layer 1: try title + description first
        slug = extract_github_slug(item.get("title", "")) or extract_github_slug(
            item.get("description", "")
        )

        # Layer 2: fetch full body_markdown if no slug found yet
        if not slug:
            try:
                time.sleep(0.3)
                detail = requests.get(
                    ARTICLE_URL.format(devto_id), headers=headers, timeout=10
                ).json()
                body = detail.get("body_markdown", "")
                slug = extract_github_slug(body)
            except Exception:
                pass

        article = DevArticle(
            devto_id=devto_id,
            title=item.get("title", ""),
            url=item.get("url", ""),
            reactions=item.get("positive_reactions_count", 0),
            tags=tags,
            published_at=published_at,
        )
        idx = len(articles)
        articles.append(article)

        if slug:
            slug_map.setdefault(slug, []).append(idx)

    print(f"[DEV.to] Fetched {len(articles)} articles, {len(slug_map)} with GitHub links.")
    return articles, slug_map
