import time
import requests
from datetime import datetime, timezone
from .models import DevArticle

BASE_URL = "https://dev.to/api/articles"

# 🚀 Sets use curly braces {} for lightning-fast O(1) lookups
TARGET_TAGS = {
    "python", "javascript", "rust", "go", "machinelearning", 
    "webdev", "typescript", "devops", "docker", "kubernetes"
}

# 🚀 Sets use curly braces {}
BANNED_TAGS = {
    "lifestyle", "career", "productivity", "watercooler", "discuss",
    "motivation", "mentalhealth", "bootcamp", "beginners", "management", "softskills"
}

# 🚀 Lists use square brackets [] 
BANNED_TITLE_KEYWORDS = [
    "burnout", "productivity hack", "my journey", "how to stay motivated", 
    "quit my job", "resume tips", "interview prep", "junior developer"
]


def fetch_and_stage_dev(global_limit=100):
    """
    Optimized Pipeline: Pulls a massive global trending snapshot in 1 single 
    HTTP request, filtering high-density technical articles instantly in-memory.
    """
    print(f"[DEV.to Pipeline] Sweeping global top feed (Density limit: {global_limit})...")
    articles = []
    seen_ids = set()

    session = requests.Session()
    headers = {
        "User-Agent": "trend-intel/1.0",
        "Accept": "application/vnd.forem.api-v1+json"
    }

    params = {
        "top": 1,          
        "per_page": global_limit
    }

    try:
        response = session.get(BASE_URL, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        raw_items = response.json()
    except requests.exceptions.RequestException as e:
        print(f"[DEV.to Pipeline] Network error fetching global feed: {e}")
        return []

    for item in raw_items:
        article_id = item["id"]
        title_lower = item.get("title", "").lower()
        article_tags = [t.lower() for t in item.get("tag_list", [])]

        # 🛑 FILTER LAYER 1: Deduplication Guard
        if article_id in seen_ids:
            continue

        # 🛑 FILTER LAYER 2: Allowlist Matcher
        if not any(target in article_tags for target in TARGET_TAGS):
            continue

        # 🛑 FILTER LAYER 3: Tag Blocklist Intersection
        if any(banned_tag in article_tags for banned_tag in BANNED_TAGS):
            continue

        # 🛑 FILTER LAYER 4: Title Context Verification
        if any(keyword in title_lower for keyword in BANNED_TITLE_KEYWORDS):
            continue

        seen_ids.add(article_id)

        try:
            created_dt = datetime.fromisoformat(item["published_timestamp"].replace("Z", "+00:00"))
        except Exception:
            created_dt = datetime.now(tz=timezone.utc)

        articles.append(
            DevArticle(
                article_id=article_id,
                title=item.get("title", ""),
                url=item.get("url", ""),
                score=item.get("public_reactions_count", 0),
                tags=article_tags,
                author=item.get("user", {}).get("username", "[unknown]"),
                num_comments=item.get("comments_count", 0),
                created_at=created_dt
            )
        )

    print(f"[DEV.to Pipeline] Validation Finished. Extracted {len(articles)} pure engineering articles instantly.")
    return articles