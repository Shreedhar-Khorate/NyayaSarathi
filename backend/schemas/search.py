from pydantic import BaseModel
from typing import List, Optional


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5
    filters: Optional[dict] = None


class SearchResult(BaseModel):
    source_document: str
    excerpt: str
    score: float
    citation: str


class SearchResponse(BaseModel):
    results: List[SearchResult]
