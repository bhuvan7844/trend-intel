import os
import sys
import time
import re
from dotenv import load_dotenv
from sqlmodel import select, delete

# Load environment configs
load_dotenv()

# Import your pipeline modules
from .github_fetcher import fetch_and_stage_github
from .hacker_news_fetcher import fetch_and_stage_hn
from .reddit_fetcher import fetch_and_stage_reddit
from .models import GitHubRepo, HackerNewsStory, RedditPost
from .database import create_db_and_tables, get_session

# 🚀 DEFINE NOISE SIGNATURES
BANNED_TOPICS = {"list", "lists", "books", "resource", "resources", "awesome", "curriculum", "roadmap", "interview", "careers"}
BANNED_DESC_KEYWORDS = ["awesome list", "curated list", "collection of", "list of free", "curriculum"]

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
        # Fetch fresh, currently trending data
        github_data = fetch_and_stage_github()
        hn_data = fetch_and_stage_hn()
        reddit_data = fetch_and_stage_reddit()

        # 1. Wipe old records (Drop-and-Replace)
        session.exec(delete(GitHubRepo))
        session.exec(delete(HackerNewsStory))
        session.exec(delete(RedditPost))
        session.flush()

        # 2. Insert clean GitHub repos
        clean_repos = []
        for repo in github_data:
            if is_noisy_repository(repo):
                continue
            session.add(repo)
            clean_repos.append(repo)
        
        session.flush()

        # 3. Insert HN stories with smart linking
        for story in hn_data:
            linked_repo_name = None
            story_title_lower = story.title.lower()

            # Layer 1: Strict URL matching
            if story.url and "github.com" in story.url:
                match = re.search(r"github\.com/([^/]+/[^/]+)", story.url)
                if match:
                    potential_name = match.group(1).lower()
                    if any(r.repo_name == potential_name for r in clean_repos):
                        linked_repo_name = potential_name

            # Layer 2: Contextual Name-Drop matching
            if not linked_repo_name:
                for repo in clean_repos:
                    short_name = repo.repo_name.split('/')[-1].lower()
                    if len(short_name) > 3 and short_name in story_title_lower:
                        linked_repo_name = repo.repo_name
                        break

            story.github_repo_name = linked_repo_name
            session.add(story)

        # 4. Insert Reddit posts
        for post in reddit_data:
            session.add(post)

        session.flush()

        # 5. Compute trend_score for each repo
        all_reddit_titles = " ".join(p.title.lower() for p in reddit_data)
        for repo in clean_repos:
            short_name = repo.repo_name.split('/')[-1].lower()
            language = (repo.language or "").lower()

            # Base: normalised star count (log scale)
            import math
            star_score = math.log1p(repo.stars) * 10

            # HN signal: 50 pts per linked story
            hn_score = sum(50 for s in hn_data if s.github_repo_name == repo.repo_name)

            # Reddit signal: 30 pts per post mentioning repo name or language
            reddit_score = sum(
                30 for p in reddit_data
                if (len(short_name) > 3 and short_name in p.title.lower())
                or (len(language) > 1 and language in p.title.lower())
            )

            repo.trend_score = round(star_score + hn_score + reddit_score, 2)

        session.commit()
        print("[Database] Snapshot completely updated.")

    except Exception as e:
        session.rollback()
        print(f"\n[Database Error] Sync failed: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    # 🚀 Run exactly once and exit. No while loops.
    run_pipeline()