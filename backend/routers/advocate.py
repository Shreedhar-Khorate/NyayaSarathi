"""
NyayaSarathi Advocate Router
Advocate portal endpoints for bar professionals — case search, legal research tools,
document drafting assistance, and activity intelligence.
Protected by ADVOCATE or ADMIN role.
"""

from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, Query, HTTPException, status

from logger import get_logger
from services.auth_dependencies import require_advocate_or_admin
from schemas.dashboard import (
    AdvocateMetricsResponse,
    AdvocateActivityListResponse,
    AdvocateActivityItem,
)
from services.user_repository import (
    get_user_activities,
    count_user_activities,
)

log = get_logger("nyayasarathi.advocate_router")

router = APIRouter()


# ── GET /api/advocate/dashboard ───────────────────────────────────────────────
@router.get("/dashboard", response_model=AdvocateMetricsResponse)
async def get_advocate_dashboard(
    current_user: Dict[str, Any] = Depends(require_advocate_or_admin)
):
    """
    Advocate portal overview metrics.
    Returns the advocate's personal activity stats, research counts,
    and quick access to tools.
    """
    advocate_id = current_user["id"]

    # Personal activity counts
    total_activities = count_user_activities(user_id=advocate_id)
    recent_research = count_user_activities(user_id=advocate_id, activity_type="LEGAL_RESEARCH")
    recent_drafts = count_user_activities(user_id=advocate_id, activity_type="DRAFTING")
    recent_docs = count_user_activities(user_id=advocate_id, activity_type="DOCUMENT_UPLOAD")
    recent_ocr = count_user_activities(user_id=advocate_id, activity_type="OCR_ANALYSIS")
    predictions = count_user_activities(user_id=advocate_id, activity_type="PREDICTION")

    return AdvocateMetricsResponse(
        advocate_name=current_user.get("full_name", "Advocate"),
        organization=current_user.get("organization") or "Independent Chambers",
        designation=current_user.get("designation") or "Advocate",
        total_activities=total_activities,
        legal_research_count=recent_research,
        drafts_created=recent_drafts,
        documents_analysed=recent_docs + recent_ocr,
        predictions_run=predictions,
    )


# ── GET /api/advocate/activity ────────────────────────────────────────────────
@router.get("/activity", response_model=AdvocateActivityListResponse)
async def get_advocate_activity(
    activity_type: Optional[str] = Query(None, description="Filter: LEGAL_RESEARCH, DRAFTING, etc."),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: Dict[str, Any] = Depends(require_advocate_or_admin),
):
    """
    Paginated activity log scoped strictly to the requesting advocate's own session.
    Advocates cannot view other users' activities.
    """
    advocate_id = current_user["id"]
    total = count_user_activities(user_id=advocate_id, activity_type=activity_type)
    activities = get_user_activities(
        user_id=advocate_id,
        activity_type=activity_type,
        limit=limit,
        offset=offset,
    )
    return AdvocateActivityListResponse(
        total=total,
        items=[
            AdvocateActivityItem(
                id=str(a["id"]),
                activity_type=a["activity_type"],
                title=a["title"],
                query_text=a.get("query_text"),
                resource_id=str(a["resource_id"]) if a.get("resource_id") else None,
                metadata=a.get("metadata") or {},
                created_at=str(a.get("created_at", "")),
            )
            for a in activities
        ],
        limit=limit,
        offset=offset,
    )
