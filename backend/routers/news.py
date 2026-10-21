"""
NyayaSarathi News Router — GET /api/news

Returns categorised Indian legal news sourced from GNews API,
with curated links to official Indian judiciary portals.
"""

from typing import Literal
from fastapi import APIRouter, HTTPException, Query, status

from logger import get_logger
from schemas.news import NewsResponse
from services.news_service import fetch_legal_news, get_valid_categories, VALID_CATEGORIES

log = get_logger("nyayasarathi.news_router")

router = APIRouter()


@router.get(
    "/",
    response_model=NewsResponse,
    summary="Fetch Indian Legal News",
    description=(
        "Returns the latest Indian legal and judiciary news from GNews API, "
        "categorised by court or topic. Includes curated links to official Indian "
        "government and court portals. Results are cached for 5 minutes."
    ),
)
async def get_news(
    category: str = Query(
        default="all",
        description=(
            "News category: 'all', 'supreme-court', 'high-courts', 'legal', 'government'."
        ),
    ),
    limit: int = Query(
        default=10,
        ge=1,
        le=20,
        description="Number of articles to return (1–20).",
    ),
) -> NewsResponse:
    """
    GET /api/news

    Query Parameters:
    - category: all | supreme-court | high-courts | legal | government
    - limit: 1–20 (default 10)
    """
    cat = category.lower().strip()
    if cat not in VALID_CATEGORIES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Invalid category '{category}'. "
                f"Choose from: {', '.join(sorted(VALID_CATEGORIES))}."
            ),
        )

    try:
        response = fetch_legal_news(category=cat, limit=limit)
        return response
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err),
        )
    except Exception:
        log.error("Unexpected error fetching legal news", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Legal news is temporarily unavailable. Please try again shortly.",
        )


@router.get(
    "/categories",
    summary="List Valid News Categories",
    description="Returns the list of valid category slugs accepted by GET /api/news.",
)
async def list_categories() -> dict:
    return {"categories": get_valid_categories()}
