import math
import re
import time
from dotenv import load_dotenv
from sqlmodel import delete

# Load environment configurations
load_dotenv()

# Import pipeline modules
from .github_fetcher import fetch_and_stage_github  # noqa: E402
from .hacker_news_fetcher import fetch_and_stage_hn  # noqa: E402
from .dev_fetcher import fetch_and_stage_dev  # 🚀 Switched from Reddit to DEV.to
from .models import GitHubRepo, HackerNewsStory, DevArticle  # 🚀 Models updated
from .database import create_db_and_tables, get_session  # noqa: E402

# 🚀 GITHUB NOISE SIGNATURES
BANNED_TOPICS = {
    "list", "lists", "books", "resource", "resources", 
    "awesome", "curriculum", "roadmap", "interview", "careers",
}
BANNED_DESC_KEYWORDS = [
    "awesome list", "curated list", "collection of", 
    "list of free", "curriculum",
]


def is_noisy_repository(repo: GitHubRepo) -> bool:
    """Evaluates if a repository is a static resource or link aggregator."""
    repo_topics = [topic.lower() for topic in (repo.topics or [])]
    if any(banned in repo_topics for banned in BANNED_TOPICS):
        return True
    description = (repo.description or "").lower()
    if any(keyword in description for keyword in BANNED_DESC_KEYWORDS):
        return True
    return False


def run_pipeline():
    print(f"\nRefreshing Trending Snapshots: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    create_db_and_tables()
    session_generator = get_session()
    session = next(session_generator)

    try:
        # Step 1: Ingest fresh telemetry streams from APIs
        github_data = fetch_and_stage_github()
        hn_data = fetch_and_stage_hn()
        dev_data = fetch_and_stage_dev()  # 🚀 Aggregating technical DEV.to data

        # Step 2: Atomic Drop-and-Replace Transaction Phase
        session.exec(delete(GitHubRepo))
        session.exec(delete(HackerNewsStory))
        session.exec(delete(DevArticle))  # 🚀 Purge stale DEV records
        session.flush()

        # Step 3: Insert sanitized GitHub Repositories
        clean_repos = []
        for repo in github_data:
            if is_noisy_repository(repo):
                continue
            session.add(repo)
            clean_repos.append(repo)

        session.flush()

        # Step 4: Map & Insert HN Stories with Cross-Network Link Checking
        for story in hn_data:
            linked_repo_name = None
            story_title_lower = story.title.lower()

            # Hard relationship resolution via explicit URLs
            if story.url and "github.com" in story.url:
                match = re.search(r"github\.com/([^/]+/[^/]+)", story.url)
                if match:
                    potential_name = match.group(1).lower()
                    if any(r.repo_name == potential_name for r in clean_repos):
                        linked_repo_name = potential_name

            # Soft relationship resolution via text token mapping
            if not linked_repo_name:
                for repo in clean_repos:
                    short_name = repo.repo_name.split("/")[-1].lower()
                    if len(short_name) > 3 and short_name in story_title_lower:
                        linked_repo_name = repo.repo_name
                        break

            story.github_repo_name = linked_repo_name
            session.add(story)

        # Step 5: Insert sanitized DEV.to engineering articles
        for article in dev_data:
            session.add(article)

        session.flush()

        # Step 6: Multi-Signal Composite trend_score Synthesis
        print("[Database] Quantifying cross-platform trend signals...")
        for repo in clean_repos:
            short_name = repo.repo_name.split("/")[-1].lower()
            language = (repo.language or "").lower()

            # Base Metric: Star volume dampened by logarithmic log1p scaling curve
            star_score = math.log1p(repo.stars) * 10

            # Signal Matrix 1: Intense, focused Hacker News discussions (+50 flat weights)
            hn_score = sum(50 for s in hn_data if s.github_repo_name == repo.repo_name)

            # Signal Matrix 2: Community Traction Velocity (DEV.to Platform)
            # Scaled dynamically via math.log1p based on the engagement (reaction count)
            dev_score = 0.0
            for a in dev_data:
                # Flag positive if project name hits title OR language perfectly overlaps metadata tags
                is_name_match = len(short_name) > 3 and short_name in a.title.lower()
                is_lang_match = len(language) > 1 and language in [tag.lower() for tag in (a.tags or [])]

                if is_name_match or is_lang_match:
                    # Dynamically weights viral technical content heavier than 0-reaction posts
                    article_engagement_weight = 30 * (1 + math.log1p(a.score / 10))
                    dev_score += article_engagement_weight

            # Compile into final database snapshot telemetry
            repo.trend_score = round(star_score + hn_score + dev_score, 2)

        session.commit()
        print("[Database] Telemetry update transaction committed successfully.")

    except Exception as e:
        session.rollback()
        print(f"\n[Database Fault] Snapshot transaction failure. Rolling back: {e}")
    finally:
        session.close()


if __name__ == "__main__":
    run_pipeline()