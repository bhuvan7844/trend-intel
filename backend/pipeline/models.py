from datetime import datetime
from typing import Optional, List
from sqlmodel import SQLModel, Field, JSON


class Repo(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)  # owner/repo
    url: str = Field(unique=True)
    description: Optional[str] = None
    language: Optional[str] = None
    stars: int = Field(default=0)
    forks: int = Field(default=0)
    source: str = Field(default="github")  # enum: github | gitlab | npm
    trending_score: float = Field(default=0.0)
    first_seen_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Snapshot(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    repo_id: int = Field(foreign_key="repo.id", index=True)
    stars: int
    recorded_at: datetime = Field(default_factory=datetime.utcnow)


class HNStory(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    object_id: str = Field(unique=True, index=True)  # HN's own ID for dedup
    title: str
    url: Optional[str] = None
    points: int = Field(default=0)
    author: str
    created_at: datetime
    fetched_at: datetime = Field(default_factory=datetime.utcnow)
    repo_id: Optional[int] = Field(default=None, foreign_key="repo.id")


class DevArticle(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    devto_id: int = Field(unique=True, index=True)  # DEV.to's own ID for dedup
    title: str
    url: str
    reactions: int = Field(default=0)
    tags: Optional[List[str]] = Field(default=None, sa_type=JSON)
    published_at: datetime
    fetched_at: datetime = Field(default_factory=datetime.utcnow)
    repo_id: Optional[int] = Field(default=None, foreign_key="repo.id")


class Mention(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    repo_id: int = Field(foreign_key="repo.id", index=True)
    source: str  # "hn" | "devto"
    # Plain int — join to hn_stories or devto_articles based on source column
    source_article_id: int
    title: str
    url: Optional[str] = None
    score: int = Field(default=0)  # points (HN) or reactions (DEV.to)
    created_at: datetime


class Topic(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    weekly_count: int = Field(default=0)
    total_count: int = Field(default=0)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
