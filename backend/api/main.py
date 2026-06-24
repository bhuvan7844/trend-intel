import sys
from collections import defaultdict
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Optional
from fastapi import FastAPI, Depends, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware  # Added for frontend cross-origin requests
from sqlmodel import Session, select
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from pydantic import BaseModel
from dotenv import load_dotenv
from google import genai
from google.genai.errors import APIError

# Corrected runtime file mapping resolution reference
BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.append(str(BACKEND_ROOT))

env_path = BACKEND_ROOT / ".env"
load_dotenv(dotenv_path=env_path, override=True)

from pipeline.database import engine, create_db_and_tables  # noqa: E402
from pipeline.models import Repo, HNStory, DevArticle, Mention, Topic  # noqa: E402
from pipeline.pipeline_manager import run_pipeline  # noqa: E402
from pipeline.scheduler import start_scheduler  # noqa: E402

try:
    ai_client = genai.Client()
except Exception as e:
    ai_client = None
    print(f"[Warning] Gemini init failed: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    run_pipeline()
    scheduler = start_scheduler()
    yield
    scheduler.shutdown()


app = FastAPI(
    title="Developer Trend Intelligence API",
    version="2.0.0",
    lifespan=lifespan,
)

# ── Enable CORS Middleware ──────────────────────────────────────────────────
# This allows your Vite/React frontend application to fetch your data cleanly.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins. For production, restrict to your deployed Vercel link.
    allow_credentials=True,
    allow_methods=["*"],  # Allows GET, POST, OPTIONS, etc.
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    query: str


def get_db():
    with Session(engine) as session:
        yield session


# ── Trending repos ranked by score ──────────────────────────────────────────
@app.get("/trending", response_model=List[Repo])
def get_trending(
    limit: int = 20,
    language: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    statement = select(Repo)
    if language:
        statement = statement.where(Repo.language.ilike(language))
    statement = statement.order_by(Repo.trending_score.desc()).limit(limit)
    return db.exec(statement).all()


# ── HN stories ──────────────────────────────────────────────────────────────
@app.get("/trends/hn", response_model=List[HNStory])
def get_hn_trends(limit: int = 20, db: Session = Depends(get_db)):
    return db.exec(
        select(HNStory).order_by(HNStory.points.desc()).limit(limit)
    ).all()


# ── DEV.to articles ──────────────────────────────────────────────────────────
@app.get("/trends/devto", response_model=List[DevArticle])
def get_devto_trends(
    limit: int = 20,
    tag: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    statement = select(DevArticle)
    if tag:
        statement = statement.where(DevArticle.tags.like(f"%{tag.lower()}%"))
    statement = statement.order_by(DevArticle.reactions.desc()).limit(limit)
    return db.exec(statement).all()


# ── Repo search ──────────────────────────────────────────────────────────────
@app.get("/search", response_model=List[Repo])
def search_repos(
    q: str = Query(..., min_length=2),
    db: Session = Depends(get_db),
):
    return db.exec(
        select(Repo)
        .where(Repo.name.ilike(f"%{q}%"))
        .order_by(Repo.trending_score.desc())
        .limit(20)
    ).all()


# ── Recommend similar repos via TF-IDF ──────────────────────────────────────
@app.get("/recommend/{repo_id}", response_model=List[Repo])
def recommend_repos(
    repo_id: int,
    limit: int = 5,
    db: Session = Depends(get_db),
):
    target = db.get(Repo, repo_id)
    if not target:
        raise HTTPException(status_code=404, detail="Repo not found")

    all_repos = db.exec(select(Repo)).all()
    if len(all_repos) < 2:
        return []

    # Build corpus: name + description + language for each repo
    def corpus_text(r: Repo) -> str:
        return f"{r.name} {r.description or ''} {r.language or ''}"

    corpus = [corpus_text(r) for r in all_repos]
    target_idx = next((i for i, r in enumerate(all_repos) if r.id == repo_id), None)
    if target_idx is None:
        return []

    tfidf = TfidfVectorizer(stop_words="english")
    matrix = tfidf.fit_transform(corpus)
    scores = cosine_similarity(matrix[target_idx], matrix).flatten()

    # Get top N similar repos excluding the target itself
    similar_indices = scores.argsort()[::-1]
    results = [
        all_repos[i] for i in similar_indices
        if all_repos[i].id != repo_id
    ][:limit]
    return results


# ── Analytics ────────────────────────────────────────────────────────────────
@app.get("/analytics")
def get_analytics(db: Session = Depends(get_db)):
    repos = db.exec(select(Repo)).all()
    mentions = db.exec(select(Mention)).all()
    topics = db.exec(select(Topic).order_by(Topic.weekly_count.desc()).limit(20)).all()

    # Source breakdown
    hn_mentions = [m for m in mentions if m.source == "hn"]
    dev_mentions = [m for m in mentions if m.source == "devto"]

    # Language distribution across all repos
    lang_counts: dict = defaultdict(int)
    for r in repos:
        if r.language:
            lang_counts[r.language] += 1
    top_languages = sorted(lang_counts.items(), key=lambda x: x[1], reverse=True)[:10]

    # Repos added per day (last 7 days)
    cutoff = datetime.now(tz=timezone.utc) - timedelta(days=7)
    daily_counts: dict = defaultdict(int)
    for r in repos:
        first_seen = r.first_seen_at
        if first_seen.tzinfo is None:
            first_seen = first_seen.replace(tzinfo=timezone.utc)
        if first_seen >= cutoff:
            day = first_seen.strftime("%Y-%m-%d")
            daily_counts[day] += 1

    # Most mentioned repos
    repo_mention_counts: dict = defaultdict(int)
    for m in mentions:
        repo_mention_counts[m.repo_id] += 1
    top_mentioned_ids = sorted(repo_mention_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    top_mentioned = []
    for repo_id, count in top_mentioned_ids:
        repo = db.get(Repo, repo_id)
        if repo:
            top_mentioned.append({"repo": repo.name, "mentions": count, "score": repo.trending_score})

    return {
        "summary": {
            "total_repos": len(repos),
            "total_mentions": len(mentions),
            "hn_mentions": len(hn_mentions),
            "devto_mentions": len(dev_mentions),
            "total_topics": len(topics),
        },
        "top_languages": [
            {"language": lang, "repo_count": count} for lang, count in top_languages
        ],
        "repos_added_last_7_days": [
            {"date": day, "count": count}
            for day, count in sorted(daily_counts.items())
        ],
        "most_mentioned_repos": top_mentioned,
        "top_topics": [
            {"name": t.name, "weekly_count": t.weekly_count, "total_count": t.total_count}
            for t in topics
        ],
        "source_breakdown": {
            "hn": {
                "stories_fetched": len(db.exec(select(HNStory)).all()),
                "mentions_created": len(hn_mentions),
                "avg_score": round(sum(m.score for m in hn_mentions) / len(hn_mentions), 1) if hn_mentions else 0,
            },
            "devto": {
                "articles_fetched": len(db.exec(select(DevArticle)).all()),
                "mentions_created": len(dev_mentions),
                "avg_score": round(sum(m.score for m in dev_mentions) / len(dev_mentions), 1) if dev_mentions else 0,
            },
        },
    }


# ── Gemini AI chat ────────────────────────────────────────────────────────────
@app.post("/api/chat")
async def chat(request: ChatRequest, db: Session = Depends(get_db)):
    if not ai_client:
        raise HTTPException(status_code=500, detail="Gemini client not configured.")

    repos = db.exec(
        select(Repo).order_by(Repo.trending_score.desc()).limit(10)
    ).all()
    hn_stories = db.exec(
        select(HNStory).order_by(HNStory.points.desc()).limit(10)
    ).all()
    dev_articles = db.exec(
        select(DevArticle).order_by(DevArticle.reactions.desc()).limit(10)
    ).all()

    context = (
        "Developer Trend Intelligence Data:\n"
        f"Top Repos: {[f'{r.name} ({r.language}, score={r.trending_score})' for r in repos]}\n"
        f"Top HN Stories: {[f'{s.title} ({s.points}pts)' for s in hn_stories]}\n"
        f"Top DEV.to Articles: {[f'{a.title} ({a.reactions} reactions)' for a in dev_articles]}"
    )

    try:
        response = ai_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"{context}\n\nQuestion: {request.query}",
        )
        return {"query": request.query, "analysis": response.text}
    except APIError as e:
        raise HTTPException(status_code=400, detail=f"Gemini error: {e.message}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))