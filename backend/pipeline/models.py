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
    created_at: datetime  # 🚀 Changed to datetime for time-decay calculations
    permalink: str
    
    # 🚀 NEW COLUMN: Tracks point growth between pipeline syncs
    score_growth_6h: int = Field(default=0)

    # 🔗 FOREIGN KEY COLUMN: Links this story to a specific GitHub repository
    # It is Optional because most HN stories do not link to a GitHub repository.
    github_repo_name: Optional[str] = Field(default=None, foreign_key="githubrepo.repo_name")

    # 🔗 RELATIONSHIP: Easily access the matching GitHubRepo instance directly from the story object
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
    
    # 🚀 Tracks stars gained in the last 24 hours
    stars_growth_24h: int = Field(default=0)

    # 🔗 RELATIONSHIP: Access a list of all HN stories discussing this repository
    stories: List[HackerNewsStory] = Relationship(back_populates="github_repo")