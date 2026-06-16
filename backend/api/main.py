import sys
from pathlib import Path
from typing import List, Optional
from fastapi import FastAPI, Depends, Query, HTTPException
from sqlmodel import Session, select, and_, not_
from pydantic import BaseModel
from dotenv import load_dotenv
from google import genai
from google.genai.errors import APIError

# ==========================================
# 1. ROBUST ABSOLUTE PATH RESOLUTION MATRIX
# ==========================================
CURRENT_FILE_PATH = Path(__file__).resolve()
# main.py sits in backend/api/, so its grand-parent is the 'backend' project root
BACKEND_ROOT = CURRENT_FILE_PATH.parent.parent

if str(BACKEND_ROOT) not in sys.path:
    sys.path.append(str(BACKEND_ROOT))

# Force load environment strings directly using absolute mapping keys
env_path = BACKEND_ROOT / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path, override=True)
else:
    print(f"[Warning] Environment matrix file not found at expected node: {env_path}")

# Local package telemetry maps
from pipeline.database import engine  # noqa: E402
from pipeline.models import GitHubRepo, HackerNewsStory, DevArticle  # noqa: E402

# ==========================================
# 2. INITIALIZE GEMINI INTELLIGENCE SYSTEM
# ==========================================
try:
    # Client seamlessly grabs the loaded GEMINI_API_KEY environment token
    ai_client = genai.Client()
except Exception as e:
    ai_client = None
    print(f"[Engine Fault] Initializing Gemini failed on missing/invalid keys: {e}")

app = FastAPI(
    title="Developer Trend Intelligence API",
    description="API endpoints serving trending GitHub repositories, HN stories, and DEV.to articles with cross-platform signal linking.",
    version="1.7.0",
)


class ChatRequest(BaseModel):
    query: str


def get_db_session():
    with Session(engine) as session:
        yield session


# ==========================================
# 3. CORE ENDPOINT ARCHITECTURE
# ==========================================

@app.get("/trends/scored", response_model=List[GitHubRepo])
def get_scored_trends(limit: int = 20, db: Session = Depends(get_db_session)):
    """Returns repos ranked by composite trend_score (stars + HN + DEV.to signals)."""
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


@app.get("/trends/devto", response_model=List[DevArticle])
def get_devto_trends(
    limit: int = 20,
    tag: Optional[str] = Query(None, description="Filter by a specific DEV.to tag (e.g., 'python')"),
    db: Session = Depends(get_db_session),
):
    """Retrieves DEV.to trending articles sorted by reactions score."""
    statement = select(DevArticle)
    if tag:
        # Lowercase tag lookup pattern to capture robust text strings within serialized lists
        statement = statement.where(DevArticle.tags.like(f'%{tag.lower()}%'))
    statement = statement.order_by(DevArticle.score.desc()).limit(limit)
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


# ==========================================
# 4. ADVANCED ASYNC TELEMETRY CHAT ANALYSIS
# ==========================================

@app.post("/api/chat")
async def analyze_trends_with_ai(request: ChatRequest, db: Session = Depends(get_db_session)):
    """
    Asynchronously passes aggregated ecosystem telemetry signals down to 
    the Gemini Intelligence Engine for cross-network analysis.
    """
    if not ai_client:
        raise HTTPException(
            status_code=500, 
            detail="Gemini runtime client not configured. Ensure your .env contains an explicit GEMINI_API_KEY."
        )

    # 1. Fetch data snapshots
    repos = db.exec(
        select(GitHubRepo).order_by(GitHubRepo.trend_score.desc()).limit(10)
    ).all()
    stories = db.exec(
        select(HackerNewsStory).order_by(HackerNewsStory.score.desc()).limit(10)
    ).all()
    articles = db.exec(
        select(DevArticle).order_by(DevArticle.score.desc()).limit(10)
    ).all()

    # 2. Fetch explicit cross-references
    linked_data = db.exec(
        select(HackerNewsStory, GitHubRepo).join(
            GitHubRepo, HackerNewsStory.github_repo_name == GitHubRepo.repo_name
        )
    ).all()

    # 3. Calculate dynamic macro-trends across ecosystems (HN + DEV.to tags)
    unique_languages = {r.language for r in repos if r.language}
    macro_trends_summary = []

    for lang in unique_languages:
        lang_lower = lang.lower()
        matching_hn = [s.title for s in stories if lang_lower in s.title.lower()]
        
        # Secured structural fallback to prevent serialization issues from crashing string loops
        matching_dev = []
        for a in articles:
            raw_tags = a.tags if isinstance(a.tags, list) else []
            tags_lower = [str(t).lower() for t in raw_tags]
            if lang_lower in tags_lower or lang_lower in a.title.lower():
                matching_dev.append(a.title)
        
        signals = []
        if matching_hn:
            signals.append(f"HN topics: {matching_hn}")
        if matching_dev:
            signals.append(f"DEV.to articles: {matching_dev}")
            
        if signals:
            macro_trends_summary.append(
                f"Language Ecosystem '{lang}' is trending across networks: {' | '.join(signals)}"
            )

    # 4. Construct layered context for Gemini prompt matrix
    linked_info = [
        f"'{item[1].repo_name}' is explicitly mentioned in '{item[0].title}'"
        for item in linked_data
    ]

    context = (
        "Trend Analysis Data System:\n"
        f"1. Verified Direct Matches: {', '.join(linked_info) if linked_info else 'None currently'}\n"
        f"2. Broad Macro-Ecosystem Signals: {'; '.join(macro_trends_summary) if macro_trends_summary else 'No shared technology topics today'}\n"
        f"3. Top Trending GitHub Repos: {[f'{r.repo_name} ({r.language})' for r in repos]}\n"
        f"4. Top Trending HN Stories: {[s.title for s in stories]}\n"
        f"5. Top Trending DEV.to Articles: {[f'{a.title} (Tags: {a.tags})' for a in articles]}"
    )

    try:
        # Run model extraction under asynchronous threading models safely
        response = ai_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"{context}\n\nUser Question: {request.query}",
        )
        return {"query": request.query, "analysis": response.text}
    except APIError as e:
        raise HTTPException(status_code=400, detail=f"Google GenAI Core Exception: {e.message}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to extract analysis stream: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)