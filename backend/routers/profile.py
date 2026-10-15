"""
NyayaSarathi Profile & History Router
Protected endpoints:
  - GET    /api/profile/me        -> Retrieve authenticated member's profile
  - PATCH  /api/profile/me        -> Update permitted profile fields (organization, designation, avatar, etc.)
  - POST   /api/profile/complete  -> Complete initial profile onboarding
  - GET    /api/history           -> Retrieve paginated user activity history
  - POST   /api/history           -> Record an activity (for client flows)
  - DELETE /api/history/{id}      -> Delete specific user activity record
"""

from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, Depends, Query, status

from logger import get_logger
from schemas.auth import (
    UserProfile,
    ProfileUpdateRequest,
    ProfileCompleteRequest,
    ActivityHistoryItem,
    ActivityHistoryListResponse,
    ActivityCreateRequest,
)
from routers.auth import get_current_user
from services.user_repository import (
    get_user_by_id,
    update_user_profile,
    create_activity,
    get_user_activities,
    delete_activity_by_id,
)

log = get_logger("nyayasarathi.profile_router")

router = APIRouter()


def _format_user_profile(user: Dict[str, Any]) -> UserProfile:
    """Helper to convert database row dict to typed UserProfile response."""
    return UserProfile(
        id=user["id"],
        email=user["email"],
        full_name=user.get("full_name", ""),
        role=user.get("role", "USER"),
        avatar_url=user.get("avatar_url"),
        organization=user.get("organization"),
        designation=user.get("designation"),
        profile_completed=bool(user.get("profile_completed", False)),
        created_at=str(user.get("created_at", "")),
        updated_at=str(user.get("updated_at", "")),
    )


# ── Profile Endpoints ────────────────────────────────────────────────────────

@router.get("/me", response_model=UserProfile, summary="Get current user profile")
async def get_my_profile(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Retrieve full profile details of the currently authenticated member."""
    # Always fetch latest from database to avoid stale JWT cache
    user = get_user_by_id(current_user["id"])
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User account not found."
        )
    return _format_user_profile(user)


@router.patch("/me", response_model=UserProfile, summary="Update permitted profile fields")
async def update_my_profile(
    req: ProfileUpdateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Update permitted profile fields (full_name, organization, designation, avatar_url).
    Strictly forbids role elevation or identity tampering.
    """
    user_id = current_user["id"]

    updated = update_user_profile(
        user_id=user_id,
        full_name=req.full_name,
        avatar_url=req.avatar_url,
        organization=req.organization,
        designation=req.designation,
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile."
        )

    log.info(f"User profile updated: {current_user['email']}", extra={"component": "PROFILE"})
    return _format_user_profile(updated)


@router.post("/complete", response_model=UserProfile, summary="Complete profile onboarding")
async def complete_my_profile(
    req: ProfileCompleteRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Complete initial profile onboarding with verified credentials.
    Marks profile_completed = TRUE in the persistent database.
    """
    user_id = current_user["id"]

    updated = update_user_profile(
        user_id=user_id,
        full_name=req.full_name,
        organization=req.organization,
        designation=req.designation,
        avatar_url=req.avatar_url,
        profile_completed=True,
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save profile completion."
        )

    # Automatically record onboarding milestone in user history
    create_activity(
        user_id=user_id,
        activity_type="PROFILE_ONBOARDING",
        title="Profile Onboarding Completed",
        metadata={
            "organization": req.organization,
            "designation": req.designation,
        },
    )

    log.info(f"Profile onboarding completed: {current_user['email']}", extra={"component": "PROFILE"})
    return _format_user_profile(updated)


# ── Activity History Endpoints ────────────────────────────────────────────────

@router.get("/history", response_model=ActivityHistoryListResponse, summary="Get user activity history")
async def get_my_history(
    activity_type: Optional[str] = Query(None, description="Filter by type (e.g. LEGAL_RESEARCH, OCR_ANALYSIS, PREDICTION)"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Retrieve isolated, authenticated activity history for the current member.
    Survives reload, logout, and subsequent logins.
    """
    user_id = current_user["id"]
    rows = get_user_activities(
        user_id=user_id,
        activity_type=activity_type,
        limit=limit,
        offset=offset,
    )

    items = [
        ActivityHistoryItem(
            id=r["id"],
            user_id=r["user_id"],
            activity_type=r["activity_type"],
            title=r["title"],
            query_text=r.get("query_text"),
            resource_id=r.get("resource_id"),
            metadata=r.get("metadata") or {},
            created_at=str(r.get("created_at", "")),
        )
        for r in rows
    ]

    return ActivityHistoryListResponse(total=len(items), items=items)


@router.post("/history", response_model=ActivityHistoryItem, status_code=status.HTTP_201_CREATED, summary="Record activity")
async def record_my_activity(
    req: ActivityCreateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Record an authenticated research or document activity.
    User ID is derived strictly from the verified JWT token.
    """
    record = create_activity(
        user_id=current_user["id"],
        activity_type=req.activity_type,
        title=req.title,
        query_text=req.query_text,
        resource_id=req.resource_id,
        metadata=req.metadata,
    )

    return ActivityHistoryItem(
        id=record["id"],
        user_id=record["user_id"],
        activity_type=record["activity_type"],
        title=record["title"],
        query_text=record.get("query_text"),
        resource_id=record.get("resource_id"),
        metadata=record.get("metadata") or {},
        created_at=str(record.get("created_at", "")),
    )


@router.delete("/history/{activity_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete activity item")
async def delete_my_activity(
    activity_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Delete an activity history record owned by the authenticated member."""
    success = delete_activity_by_id(activity_id, user_id=current_user["id"])
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activity record not found or access denied."
        )
    return None
