from pathlib import Path
import sys
from typing import List, Optional
from fastapi import FastAPI, Depends, Query, HTTPException
from sqlmodel import Session, select, and_, not_
from pydantic import BaseModel
from dotenv import load_dotenv
from google import genai

# Resolve paths
API_DIR = Path(__file__).resolve().parent
BACKEND_DIR = API_DIR.parent
sys.path.append(str(BACKEND_DIR))

# Load .env file
load_dotenv(BACKEND_DIR / ".env")

from pipeline.database import engine  # noqa: E402
from pipeline.models import GitHubRepo, HackerNewsStory, RedditPost  # noqa: E402

# Initialize Gemini Client
try:
    ai_client = genai.Client()
except Exception as e:
    ai_client = None
    print(f"Error initializing Gemini: {e}")

app = FastAPI(
    title="Developer Trend Intelligence API",
    description="API endpoints serving trending GitHub repositories and HN stories with cross-platform signal linking.",
    version="1.6.0",
)


class ChatRequest(BaseModel):
    query: str


def get_db_session():
    with Session(engine) as session:
        yield session


@app.get("/trends/scored", response_model=List[GitHubRepo])
def get_scored_trends(limit: int = 20, db: Session = Depends(get_db_session)):
    """Returns repos ranked by composite trend_score (stars + HN + Reddit signals)."""
    statement = (
        select(GitHubRepo)
        .where(
            and_(
                GitHubRepo.language.is_not(None),
                not_(GitHubRepo.language == "Markdown"),
            )
        )
        .order_by(GitHubRepo.trend_score.desc())
        .limit(limit)
    )
    return db.exec(statement).all()


@app.get("/trends/github", response_model=List[GitHubRepo])
def get_github_trends(
    limit: int = 10,
    trending_on_hn: bool = Query(
        False, description="Only show repos explicitly discussed on HN"
    ),
    db: Session = Depends(get_db_session),
):
    """Retrieves repos sorted by 24h star growth. Optional: Filter by explicit HN linkage."""
    statement = select(GitHubRepo).where(
        and_(GitHubRepo.language.is_not(None), not_(GitHubRepo.language == "Markdown"))
    )

    if trending_on_hn:
        statement = statement.join(GitHubRepo.stories).distinct()

    statement = statement.order_by(GitHubRepo.stars_growth_24h.desc()).limit(limit)
    return db.exec(statement).all()


@app.get("/trends/reddit", response_model=List[RedditPost])
def get_reddit_trends(
    limit: int = 20,
    subreddit: Optional[str] = Query(None, description="Filter by subreddit name"),
    db: Session = Depends(get_db_session),
):
    """Retrieves Reddit posts sorted by score."""
    statement = select(RedditPost)
    if subreddit:
        statement = statement.where(RedditPost.subreddit.ilike(subreddit))
    statement = statement.order_by(RedditPost.score.desc()).limit(limit)
    return db.exec(statement).all()


@app.get("/trends/hn", response_model=List[HackerNewsStory])
def get_hacker_news_trends(limit: int = 10, db: Session = Depends(get_db_session)):
    """Retrieves HN stories sorted by 6h score growth velocity."""
    statement = (
        select(HackerNewsStory)
        .order_by(HackerNewsStory.score_growth_6h.desc())
        .limit(limit)
    )
    return db.exec(statement).all()


@app.get("/api/repositories/{repo_name}/contextual-trends")
def get_repository_contextual_trends(
    repo_name: str, db: Session = Depends(get_db_session)
):
    """
    🚀 STRATEGY 2 FALLBACK ENDPOINT:
    Fetches direct links for a repository. If none exist, falls back to matching
    Hacker News stories discussing the repository's programming language.
    """
    # SQLite parameters are path-friendly, but we match lower for safety
    normalized_name = repo_name.lower()
    statement = select(GitHubRepo).where(GitHubRepo.repo_name == normalized_name)
    repo = db.exec(statement).first()

    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    # Layer 1: Check for explicit, hard relationships
    direct_stories = repo.stories
    if direct_stories:
        return {
            "repo_name": repo.repo_name,
            "match_type": "direct",
            "stories": direct_stories,
        }

    # Layer 2: Fall back to matching macro-trends via programming language
    fallback_stories = []
    if repo.language:
        hn_statement = (
            select(HackerNewsStory)
            .where(HackerNewsStory.title.ilike(f"%{repo.language}%"))
            .order_by(HackerNewsStory.score_growth_6h.desc())
            .limit(5)
        )
        fallback_stories = db.exec(hn_statement).all()

    return {
        "repo_name": repo.repo_name,
        "match_type": "macro_ecosystem",
        "matched_language": repo.language,
        "stories": fallback_stories,
    }


@app.get("/api/debug/links")
def debug_links(db: Session = Depends(get_db_session)):
    """Returns a list of all HN stories with an assigned hard link to a GitHub repository."""
    statement = select(HackerNewsStory).where(
        HackerNewsStory.github_repo_name.is_not(None)
    )
    results = db.exec(statement).all()
    return [{"story": s.title, "linked_repo": s.github_repo_name} for s in results]


@app.post("/api/chat")
def analyze_trends_with_ai(request: ChatRequest, db: Session = Depends(get_db_session)):
    if not ai_client:
        raise HTTPException(status_code=500, detail="Gemini client not configured.")

    # 1. Fetch general trends
    repos = db.exec(
        select(GitHubRepo).order_by(GitHubRepo.stars_growth_24h.desc()).limit(10)
    ).all()
    stories = db.exec(
        select(HackerNewsStory)
        .order_by(HackerNewsStory.score_growth_6h.desc())
        .limit(10)
    ).all()

    # 2. Fetch direct explicit cross-references
    linked_data = db.exec(
        select(HackerNewsStory, GitHubRepo).join(
            GitHubRepo, HackerNewsStory.github_repo_name == GitHubRepo.repo_name
        )
    ).all()

    # 3. Calculate dynamic macro-trends to feed the AI context pool
    unique_languages = {r.language for r in repos if r.language}
    macro_trends_summary = []

    for lang in unique_languages:
        # In-memory evaluation of matching topics to keep pipeline lightning fast
        matching_hn = [s.title for s in stories if lang.lower() in s.title.lower()]
        if matching_hn:
            macro_trends_summary.append(
                f"Language Ecosystem '{lang}' is hot on HN with discussions like: {matching_hn}"
            )

    # 4. Construct layered architectural context
    linked_info = [
        f"'{item[1].repo_name}' is explicitly mentioned in '{item[0].title}'"
        for item in linked_data
    ]

    context = (
        "Trend Analysis Data System:\n"
        f"1. Verified Direct Matches: {', '.join(linked_info) if linked_info else 'None currently'}\n"
        f"2. Broad Macro-Ecosystem Signals: {'; '.join(macro_trends_summary) if macro_trends_summary else 'No shared technology topics today'}\n"
        f"3. Top Trending GitHub Repos: {[f'{r.repo_name} ({r.language})' for r in repos]}\n"
        f"4. Top Trending HN Stories: {[s.title for s in stories]}"
    )

    try:
        response = ai_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"{context}\n\nUser Question: {request.query}",
        )
        return {"query": request.query, "analysis": response.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
