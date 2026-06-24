import re
import requests
from datetime import datetime, timedelta, timezone
from .models import HNStory

ALGOLIA_URL = "https://hn.algolia.com/api/v1/search_by_date"
GITHUB_PATTERN = re.compile(r"github\.com/([a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+)")


def extract_github_slug(text: str) -> str | None:
    match = GITHUB_PATTERN.search(text or "")
    if not match:
        return None
    slug = match.group(1).lower().rstrip(".git")
    # filter out github.com/orgs, github.com/topics etc.
    if any(slug.startswith(p) for p in ("orgs/", "topics/", "collections/")):
        return None
    return slug


def fetch_hn_stories(limit=500) -> tuple[list[HNStory], dict[str, list]]:
    """
    Returns:
        stories: list of HNStory objects
        slug_map: {github_slug: [story_indices]} for fast repo matching
    """
    print("[HN] Fetching stories via Algolia...")
    cutoff = (datetime.now(tz=timezone.utc) - timedelta(days=7)).timestamp()

    params = {
        "query": "github",
        "tags": "story",
        "hitsPerPage": limit,
    }

    try:
        res = requests.get(ALGOLIA_URL, params=params, timeout=10)
        res.raise_for_status()
        hits = res.json().get("hits", [])
    except requests.exceptions.RequestException as e:
        print(f"[HN] Error: {e}")
        return [], {}

    stories = []
    slug_map: dict[str, list] = {}
    seen = set()

    for hit in hits:
        object_id = hit.get("objectID")
        if object_id in seen:
            continue

        created_at = datetime.fromtimestamp(
            hit.get("created_at_i", 0), tz=timezone.utc
        )
        if created_at.timestamp() < cutoff:
            continue

        if hit.get("points", 0) <= 10:
            continue

        seen.add(object_id)

        # Try URL first, then title for GitHub slug
        slug = extract_github_slug(hit.get("url", "")) or extract_github_slug(
            hit.get("title", "")
        )

        story = HNStory(
            object_id=object_id,
            title=hit.get("title", ""),
            url=hit.get("url"),
            points=hit.get("points", 0),
            author=hit.get("author", "[unknown]"),
            created_at=created_at,
        )
        idx = len(stories)
        stories.append(story)

        if slug:
            slug_map.setdefault(slug, []).append(idx)

    print(f"[HN] Fetched {len(stories)} stories, {len(slug_map)} with GitHub links.")
    return stories, slug_map
