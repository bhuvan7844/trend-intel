from datetime import datetime, timezone
import requests
from .models import HackerNewsStory

TOP_STORIES_URL = "https://hacker-news.firebaseio.com/v0/topstories.json"
ITEM_URL = "https://hacker-news.firebaseio.com/v0/item/{}.json"


def fetch_and_stage_hn(limit=10):
    print("[Hacker News Pipeline] Fetching trending stories...")
    hn_stories = []

    session = requests.Session()

    try:
        # 1. Fetch top story IDs
        response = session.get(TOP_STORIES_URL, timeout=10)
        response.raise_for_status()
        story_ids = response.json()[:limit]

        # 2. Fetch detailed data for each top story ID
        for story_id in story_ids:
            try:
                item_response = session.get(ITEM_URL.format(story_id), timeout=5)
                item_response.raise_for_status()
                item = item_response.json()

                if item and item.get("type") == "story":
                    # 🚀 Pass the datetime object directly to the model
                    created_dt = datetime.fromtimestamp(item["time"], tz=timezone.utc)

                    hn_stories.append(
                        HackerNewsStory(
                            story_id=item["id"],
                            title=item.get("title", ""),
                            author=item.get("by", "[unknown]"),
                            score=item.get("score", 0),
                            text=item.get("text"),
                            url=item.get("url"),
                            num_comments=item.get("descendants", 0),
                            created_at=created_dt,  # Correct type for SQLModel
                            permalink=f"https://news.ycombinator.com/item?id={item['id']}",
                            score_growth_6h=0,  # Initialized to 0
                        )
                    )
            except requests.exceptions.RequestException:
                continue

        print(f"Successfully fetched {len(hn_stories)} stories from Hacker News.")
        return hn_stories

    except requests.exceptions.RequestException as e:
        print(f"Hacker News API Error: {e}")
        return []