from fastapi import APIRouter
from app.schemas.search import SearchRequest, SearchResponse
from app.services.search_service import hybrid_search

router = APIRouter()

@router.post("", response_model=SearchResponse)
def search_cases(request: SearchRequest):
    """Hybrid semantic + lexical search across legal documents."""
    return hybrid_search(request)
