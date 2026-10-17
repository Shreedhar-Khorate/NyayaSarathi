"""
NyayaSarathi Advocate Router
Advocate portal endpoints for bar professionals — case search, legal research tools,
document drafting assistance, and activity intelligence.
Protected by ADVOCATE or ADMIN role. Includes a judge-only endpoint for promoting
a USER/ADVOCATE to the JUDGE role.
"""

from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, Query, HTTPException, status

from logger import get_logger
from services.auth_dependencies import require_role, get_current_user
from schemas.dashboard import (
    AdvocateMetricsResponse,
    AdvocateActivityListResponse,
    AdvocateActivityItem,
    JudgePromoteRequest,
    RoleUpdateResponse,
)
from services.user_repository import (
    get_user_by_id,
    get_user_activities,
    count_user_activities,
    update_user_role_with_audit,
    list_users,
    count_users,
    get_admin_metrics,
)

log = get_logger("nyayasarathi.advocate_router")

router = APIRouter()

# Role dependency aliases
require_advocate_or_admin = require_role(["ADVOCATE", "ADMIN"])
require_judge = require_role(["JUDGE"])
require_judge_or_admin = require_role(["JUDGE", "ADMIN"])


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


# ── POST /api/advocate/promote-to-judge ───────────────────────────────────────
@router.post("/promote-to-judge", response_model=RoleUpdateResponse, status_code=status.HTTP_200_OK)
async def judge_promote_to_judge(
    req: JudgePromoteRequest,
    current_judge: Dict[str, Any] = Depends(require_judge),
):
    """
    **JUDGE-ONLY** endpoint to nominate a USER or ADVOCATE to the JUDGE role.
    Only sitting judges may elevate peers to judicial standing.
    Admins cannot use this endpoint — they have their own admin/users/{id}/role endpoint.
    Persists a durable audit record with the nominating judge as the actor.
    """
    target_user = get_user_by_id(req.target_user_id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID '{req.target_user_id}' does not exist.",
        )

    current_role = target_user.get("role", "USER").upper()

    # A judge cannot nominate themselves
    if target_user["id"] == current_judge["id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A judge cannot nominate themselves for judicial appointment.",
        )

    # Only USER and ADVOCATE can be elevated to JUDGE via this path
    if current_role not in {"USER", "ADVOCATE"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only users with USER or ADVOCATE roles can be promoted to JUDGE. "
                   f"Current role of '{target_user['email']}' is '{current_role}'.",
        )

    # Execute atomic role change
    audit_record = update_user_role_with_audit(
        target_user_id=req.target_user_id,
        actor_user_id=current_judge["id"],
        new_role="JUDGE",
        reason=req.reason or f"Judicial appointment by Judge {current_judge.get('full_name', current_judge['email'])}",
    )

    if not audit_record:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Role promotion failed. Please try again.",
        )

    log.info(
        f"Judge {current_judge['email']} promoted {target_user['email']} from {current_role} -> JUDGE",
        extra={"component": "JUDGE_PROMOTE"},
    )

    return RoleUpdateResponse(
        success=True,
        audit_id=audit_record["audit_id"],
        target_user_id=req.target_user_id,
        old_role=current_role,
        new_role="JUDGE",
        reason=req.reason,
        updated_at=audit_record["created_at"],
    )


# ── GET /api/advocate/eligible-for-judgeship ──────────────────────────────────
@router.get("/eligible-for-judgeship")
async def list_eligible_for_judgeship(
    search: Optional[str] = Query(None, description="Search by name or email"),
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0),
    current_judge: Dict[str, Any] = Depends(require_judge),
):
    """
    **JUDGE-ONLY** — lists USER and ADVOCATE accounts eligible for judicial promotion.
    Returns basic non-sensitive identification info to help judges nominate peers.
    """
    # Fetch advocates first, then users (excluding current judge)
    advocates = list_users(search=search, role="ADVOCATE", limit=limit // 2 + 1, offset=0)
    users = list_users(search=search, role="USER", limit=limit // 2 + 1, offset=0)

    combined = advocates + users
    # Exclude the calling judge
    combined = [u for u in combined if u["id"] != current_judge["id"]]

    eligible = [
        {
            "id": u["id"],
            "email": u["email"],
            "full_name": u.get("full_name", ""),
            "role": u.get("role", "USER"),
            "organization": u.get("organization"),
            "designation": u.get("designation"),
            "created_at": str(u.get("created_at", "")),
        }
        for u in combined[offset: offset + limit]
    ]

    return {
        "total": count_users(search=search, role="ADVOCATE") + count_users(search=search, role="USER"),
        "items": eligible,
        "limit": limit,
        "offset": offset,
    }
