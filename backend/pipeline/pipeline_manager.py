import math
import time
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from sqlmodel import Session, select, delete

load_dotenv()

from .github_fetcher import fetch_github_repos, fetch_single_repo  # noqa: E402
from .hacker_news_fetcher import fetch_hn_stories  # noqa: E402
from .dev_fetcher import fetch_devto_articles  # noqa: E402
from .models import Repo, Snapshot, HNStory, DevArticle, Mention, Topic  # noqa: E402
from .database import create_db_and_tables, engine  # noqa: E402

BANNED_TOPICS = {
    "list", "lists", "books", "resource", "resources",
    "awesome", "curriculum", "roadmap", "interview", "careers",
}
BANNED_DESC_KEYWORDS = [
    "awesome list", "curated list", "collection of", "list of free", "curriculum",
]

HN_WEIGHT = 50
DEV_WEIGHT = 30
RECENCY_BONUS = 10
RECENCY_DAYS = 7


def is_noisy(name: str, description: str) -> bool:
    name_lower = name.lower()
    if any(kw in name_lower for kw in ["awesome", "free-programming", "roadmap", "curriculum", "interview", "public-apis", "books"]):
        return True
    desc = (description or "").lower()
    return any(kw in desc for kw in BANNED_DESC_KEYWORDS)


def compute_trending_score(
    stars: int,
    hn_mentions: int,
    dev_mentions: int,
    first_seen_at: datetime,
) -> float:
    star_score = math.log1p(stars) * 10
    mention_score = (hn_mentions * HN_WEIGHT) + (dev_mentions * DEV_WEIGHT)
    cutoff = datetime.now(tz=timezone.utc) - timedelta(days=RECENCY_DAYS)
    first_seen = first_seen_at.replace(tzinfo=timezone.utc) if first_seen_at.tzinfo is None else first_seen_at
    recency = RECENCY_BONUS if first_seen >= cutoff else 0
    # Mention signal is boosted 3x to surface discussed repos above star-heavy noise
    return round(star_score + (mention_score * 3) + recency, 2)


def run_pipeline():
    print(f"\nRefreshing Trending Snapshots: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    create_db_and_tables()

    github_repos = fetch_github_repos()
    hn_stories, hn_slug_map = fetch_hn_stories()
    dev_articles, dev_slug_map = fetch_devto_articles()

    with Session(engine) as session:
        try:
            # ── 1. Upsert repos ──────────────────────────────────────────────
            repo_id_map: dict[str, int] = {}  # slug → db id

            for repo_data in github_repos:
                if is_noisy(repo_data.name, repo_data.description or ""):
                    continue
                existing = session.exec(
                    select(Repo).where(Repo.name == repo_data.name)
                ).first()

                if existing:
                    existing.stars = repo_data.stars
                    existing.forks = repo_data.forks
                    existing.description = repo_data.description
                    existing.language = repo_data.language
                    existing.updated_at = datetime.utcnow()
                    session.add(existing)
                    session.flush()
                    repo_id_map[existing.name] = existing.id
                else:
                    session.add(repo_data)
                    session.flush()
                    repo_id_map[repo_data.name] = repo_data.id

            # Fetch real metadata for repos discovered via HN/DEV links
            all_slugs = set(hn_slug_map.keys()) | set(dev_slug_map.keys())
            fetched_this_run: set[str] = set()  # cache to avoid duplicate API calls
            for slug in all_slugs:
                if slug in repo_id_map:
                    continue
                if slug in fetched_this_run:
                    continue
                fetched_this_run.add(slug)

                # Fetch real metadata from GitHub API
                repo_data = fetch_single_repo(slug)
                if repo_data is None:
                    # Repo not found on GitHub, insert minimal placeholder
                    repo_data = Repo(
                        name=slug,
                        url=f"https://github.com/{slug}",
                        source="github",
                    )

                existing = session.exec(
                    select(Repo).where(Repo.name == slug)
                ).first()
                if existing:
                    if repo_data.stars:
                        existing.stars = repo_data.stars
                        existing.forks = repo_data.forks
                        existing.description = repo_data.description
                        existing.language = repo_data.language
                        existing.updated_at = datetime.utcnow()
                    session.add(existing)
                    session.flush()
                    repo_id_map[slug] = existing.id
                else:
                    session.add(repo_data)
                    session.flush()
                    repo_id_map[slug] = repo_data.id

            print(f"[Pipeline] {len(repo_id_map)} repos in map ({len(fetched_this_run)} discovered via HN/DEV).")

            # ── 2. Record star snapshots ─────────────────────────────────────
            for slug, repo_id in repo_id_map.items():
                repo = session.get(Repo, repo_id)
                if repo:
                    session.add(Snapshot(repo_id=repo_id, stars=repo.stars))

            # ── 3. Clear stale mentions, HN stories, DEV articles ────────────
            session.exec(delete(Mention))
            session.exec(delete(HNStory))
            session.exec(delete(DevArticle))
            session.flush()

            # ── 4. Insert HN stories + build mentions ────────────────────────
            for story in hn_stories:
                session.add(story)
                session.flush()

            for slug, indices in hn_slug_map.items():
                repo_id = repo_id_map.get(slug)
                if not repo_id:
                    continue
                for idx in indices:
                    story = hn_stories[idx]
                    story.repo_id = repo_id
                    session.add(story)
                    session.add(Mention(
                        repo_id=repo_id,
                        source="hn",
                        source_article_id=story.id,
                        title=story.title,
                        url=story.url,
                        score=story.points,
                        created_at=story.created_at,
                    ))

            # ── 5. Insert DEV articles + build mentions ──────────────────────
            for article in dev_articles:
                session.add(article)
                session.flush()

            for slug, indices in dev_slug_map.items():
                repo_id = repo_id_map.get(slug)
                if not repo_id:
                    continue
                for idx in indices:
                    article = dev_articles[idx]
                    article.repo_id = repo_id
                    session.add(article)
                    session.add(Mention(
                        repo_id=repo_id,
                        source="devto",
                        source_article_id=article.id,
                        title=article.title,
                        url=article.url,
                        score=article.reactions,
                        created_at=article.published_at,
                    ))

            session.flush()

            # ── 6. Compute trending scores ───────────────────────────────────
            all_repos = session.exec(select(Repo)).all()
            for repo in all_repos:
                mentions = session.exec(
                    select(Mention).where(Mention.repo_id == repo.id)
                ).all()
                hn_count = sum(1 for m in mentions if m.source == "hn")
                dev_count = sum(1 for m in mentions if m.source == "devto")
                repo.trending_score = compute_trending_score(
                    repo.stars, hn_count, dev_count, repo.first_seen_at
                )
                session.add(repo)

            # ── 7. Update topics leaderboard ─────────────────────────────────
            tag_counts: dict[str, int] = {}
            for article in dev_articles:
                for tag in (article.tags or []):
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1

            for tag, count in tag_counts.items():
                topic = session.exec(
                    select(Topic).where(Topic.name == tag)
                ).first()
                if topic:
                    topic.weekly_count = count
                    topic.total_count += count
                    topic.updated_at = datetime.utcnow()
                else:
                    topic = Topic(name=tag, weekly_count=count, total_count=count)
                session.add(topic)

            session.commit()
            print("[Pipeline] Snapshot complete.")

        except Exception as e:
            session.rollback()
            print(f"[Pipeline Error] {e}")


if __name__ == "__main__":
    run_pipeline()
