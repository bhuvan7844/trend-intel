import xml.etree.ElementTree as ET
import requests
import time
from datetime import datetime, timezone
from .models import RedditPost

SUBREDDITS = ["programming", "MachineLearning", "Python", "webdev", "rust", "golang"]
NS = "http://www.w3.org/2005/Atom"


def fetch_and_stage_reddit(limit=10):
    print("[Reddit Pipeline] Fetching trending posts via RSS...")
    posts = []
    seen_ids = set()

    for subreddit in SUBREDDITS:
        try:
            res = requests.get(
                f"https://www.reddit.com/r/{subreddit}/hot.rss?limit={limit}",
                headers={"User-Agent": "trend-intel/1.0"},
                timeout=10
            )
            res.raise_for_status()
            root = ET.fromstring(res.content)

            for entry in root.findall(f"{{{NS}}}entry"):
                post_id = entry.findtext(f"{{{NS}}}id", "").split("_")[-1]
                title = entry.findtext(f"{{{NS}}}title", "")
                link = entry.find(f"{{{NS}}}link")
                url = link.get("href", "") if link is not None else ""
                updated = entry.findtext(f"{{{NS}}}updated", "")

                if post_id in seen_ids or not title:
                    continue
                seen_ids.add(post_id)

                try:
                    created_at = datetime.fromisoformat(updated.replace("Z", "+00:00"))
                except Exception:
                    created_at = datetime.now(tz=timezone.utc)

                posts.append(RedditPost(
                    post_id=post_id,
                    title=title,
                    url=url,
                    score=0,
                    subreddit=subreddit,
                    num_comments=0,
                    permalink=url,
                    created_at=created_at
                ))
        except Exception as e:
            print(f"[Reddit Pipeline] Error fetching r/{subreddit}: {e}")
            continue
        time.sleep(2)

    print(f"[Reddit Pipeline] Fetched {len(posts)} posts.")
    return posts
