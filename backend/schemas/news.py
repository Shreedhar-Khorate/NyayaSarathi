"""
NyayaSarathi News Schemas — Pydantic models for the Legal News API.
"""

from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel, Field


class NewsArticle(BaseModel):
    """A single normalised news article from GNews or an official court source."""

    title: str = Field(..., description="Headline of the article.")
    description: Optional[str] = Field(None, description="Short summary / snippet.")
    url: str = Field(..., description="Canonical URL of the article.")
    source_name: str = Field(..., description="Publisher name.")
    published_at: Optional[str] = Field(None, description="ISO-8601 publication timestamp.")
    image_url: Optional[str] = Field(None, description="Optional thumbnail URL.")
    category: str = Field(..., description="Category key: all | supreme-court | high-courts | legal | government.")
    story_id: Optional[str] = Field(None, description="Stable identifier of the story group this article belongs to.")


class NewsStoryGroup(BaseModel):
    """A unified story card representing a single legal matter with distinct developments."""

    story_id: str = Field(..., description="Stable deterministic ID derived from core legal matter.")
    title: str = Field(..., description="Lead / representative headline for the story group.")
    category: str = Field(..., description="Primary category.")
    primary_article: NewsArticle = Field(..., description="Lead article representing this story.")
    related_articles: List[NewsArticle] = Field(
        default_factory=list,
        description="Distinct legal updates, hearings, or alternative publisher coverage on this matter.",
    )
    coverage_count: int = Field(1, description="Total number of articles in this story group.")
    key_entities: List[str] = Field(default_factory=list, description="Extracted court, parties, or matter anchors.")
    last_updated: Optional[str] = Field(None, description="Most recent article timestamp.")


class OfficialSource(BaseModel):
    """A curated link to an official Indian government / judiciary portal."""

    name: str = Field(..., description="Human-readable name of the portal.")
    url: str = Field(..., description="Direct URL.")
    description: str = Field(..., description="One-sentence description.")


class NewsResponse(BaseModel):
    """Top-level response returned by GET /api/news."""

    category: str = Field(..., description="Requested category slug.")
    total: int = Field(..., description="Number of stories returned.")
    articles: List[NewsArticle] = Field(..., description="Normalised articles list (backward-compatible).")
    stories: List[NewsStoryGroup] = Field(
        default_factory=list,
        description="Grouped legal matter story cards with related coverage and updates.",
    )
    official_sources: List[OfficialSource] = Field(
        default_factory=list,
        description="Curated official Indian judiciary / government portals.",
    )
    disclaimer: str = Field(
        default=(
            "The articles listed are sourced from GNews and represent media coverage "
            "only. NyayaSarathi does not guarantee accuracy, completeness, or legal "
            "validity. Always verify information through official court records."
        ),
        description="Standard legal-clarity disclaimer.",
    )
    cached: bool = Field(False, description="True when response was served from cache.")
    fetched_at: Optional[str] = Field(None, description="UTC timestamp when data was fetched.")
