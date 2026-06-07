from pydantic import BaseModel, Field
from typing import List, Optional

class ExtractedTechEntity(BaseModel):
    tech_id: str = Field(
        description="Canonical lowercase slug (e.g., 'fastapi', 'next.js', 'tailwindcss', 'pytorch', 'docker'). Strip action words and user/org prefixes."
    )
    is_valid_dev_tool: bool = Field(
        description="True if it's an installable tool/framework/library/db. False for tutorials, broad concepts, blogs, or careers."
    )
    sentiment_score: int = Field(
        description="Text sentiment rating: -5 (backlash/failure) to +5 (praise/adoption). 0 for neutral technical mentions."
    )
    justification: str = Field(
        description="One-sentence logical reasoning for the extracted tech and its sentiment score."
    )

class GitHubValidationModel(BaseModel):
    tech_id: str = Field(
        description="Lowercase canonical identifier. Strip org prefix (e.g., 'tiangolo/fastapi' -> 'fastapi', 'vercel/next.js' -> 'next.js')."
    )
    is_valid_dev_tool: bool = Field(description="True if the repo is a functional software tool/framework, not a listicle or tutorial guide.")
    relevance_tags: List[str] = Field(description="Architecture categorization tags (e.g., 'orm', 'state-management', 'compiler').")

class RedditBatchResponse(BaseModel):
    mentions: List[ExtractedTechEntity] = Field(description="List of all validated engineering entities parsed from the batch.")