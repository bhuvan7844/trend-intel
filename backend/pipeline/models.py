from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field, JSON, Relationship


class HackerNewsStory(SQLModel, table=True):
    story_id: int = Field(primary_key=True)
    title: str
    author: str
    score: int
    text: Optional[str] = None
    url: Optional[str] = None
    num_comments: int
    created_at: datetime
    permalink: str
    score_growth_6h: int = Field(default=0)
    github_repo_name: Optional[str] = Field(
        default=None, foreign_key="githubrepo.repo_name"
    )
    github_repo: Optional["GitHubRepo"] = Relationship(back_populates="stories")


class GitHubRepo(SQLModel, table=True):
    repo_name: str = Field(primary_key=True)
    technology_id: str
    owner: str
    language: Optional[str] = None
    description: Optional[str] = None
    topics: Optional[List[str]] = Field(default=None, sa_type=JSON)
    stars: int
    forks: int
    watchers: int
    open_issues: int
    created_at: str
    updated_at: str
    pushed_at: str
    html_url: str
    stars_growth_24h: int = Field(default=0)
    trend_score: float = Field(default=0.0)
    stories: List[HackerNewsStory] = Relationship(back_populates="github_repo")


class RedditPost(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    post_id: str = Field(unique=True)
    title: str
    url: str
    score: int
    subreddit: str
    num_comments: int
    permalink: str
    created_at: datetime
