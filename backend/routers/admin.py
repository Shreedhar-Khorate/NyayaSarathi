"""
NyayaSarathi Admin Router
Administrative endpoints for user role management, system metrics, and audit history.
Protected strictly by server-side ADMIN authorization.
Supported roles: USER, ADVOCATE, ADMIN.
"""

from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, Depends, Query, status

from logger import get_logger
from services.auth_dependencies import require_admin
from schemas.dashboard import (
    AdminMetricsResponse,
    AdminUserListResponse,
    AdminUserItem,
    RoleUpdateRequest,
    RoleUpdateResponse,
    RoleAuditListResponse,
    RoleAuditItem,
)
from services.user_repository import (
    get_user_by_id,
    list_users,
    count_users,
    update_user_role_with_audit,
    get_role_audit_history,
    count_role_audits,
    get_admin_metrics,
    count_active_admins,
    get_db_connection,
    is_postgres_authoritative,
    get_pg_connection,
)

log = get_logger("nyayasarathi.admin_router")

router = APIRouter()


# ── GET /api/admin/dashboard ──────────────────────────────────────────────────
@router.get("/dashboard", response_model=AdminMetricsResponse)
async def get_dashboard_overview(
    current_admin: Dict[str, Any] = Depends(require_admin)
):
    """
    Fetch comprehensive administrative overview metrics derived from the database.
    Includes verified user counts by role, recent registrations, and role changes.
    """
    metrics = get_admin_metrics()
    return AdminMetricsResponse(
        total_users=metrics["total_users"],
        role_counts=metrics["role_counts"],
        recent_users=metrics["recent_users"],
        recent_role_changes=[RoleAuditItem(**a) for a in metrics["recent_role_changes"]],
        total_activities=metrics["total_activities"],
        total_judgments=metrics["total_judgments"],
    )


# ── GET /api/admin/users ──────────────────────────────────────────────────────
@router.get("/users", response_model=AdminUserListResponse)
async def get_all_users(
    search: Optional[str] = Query(None, description="Search by name or email"),
    role: Optional[str] = Query(None, description="Filter by role: USER, ADVOCATE, ADMIN"),
    limit: int = Query(50, ge=1, le=100, description="Page size limit"),
    offset: int = Query(0, ge=0, description="Offset index"),
    current_admin: Dict[str, Any] = Depends(require_admin),
):
    """
    Search and paginate all registered users. Excludes passwords and sensitive tokens.
    """
    total = count_users(search=search, role=role)
    users = list_users(search=search, role=role, limit=limit, offset=offset)
    return AdminUserListResponse(
        total=total,
        items=[AdminUserItem(**u) for u in users],
        limit=limit,
        offset=offset,
    )


# ── PATCH /api/admin/users/{user_id}/role ─────────────────────────────────────
@router.patch("/users/{user_id}/role", response_model=RoleUpdateResponse)
async def change_user_role(
    user_id: str,
    req: RoleUpdateRequest,
    current_admin: Dict[str, Any] = Depends(require_admin),
):
    """
    Change an eligible user's role and persist a durable audit record.
    Enforces safeguards against self-demotion, last-admin removal, and invalid roles.
    Allowed active roles: USER, ADVOCATE, ADMIN.
    """
    actor_id = current_admin["id"]
    new_role = req.new_role.strip().upper()
    valid_roles = {"USER", "ADVOCATE", "ADMIN"}

    if new_role not in valid_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid target role '{new_role}'. Must be one of {sorted(list(valid_roles))}.",
        )

    # 1. Target existence check
    target_user = get_user_by_id(user_id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID '{user_id}' does not exist.",
        )

    old_role = target_user.get("role", "USER").upper()

    # 2. Prevent accidental self-demotion
    if target_user["id"] == actor_id and new_role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Administrators cannot demote themselves to prevent system lockout.",
        )

    # 3. Prevent removal/demotion of the last remaining active administrator
    if old_role == "ADMIN" and new_role != "ADMIN":
        active_admins = count_active_admins()
        if active_admins <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Operation prohibited: Cannot demote the last remaining active administrator.",
            )

    # 4. Check if role is actually changing
    if old_role == new_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User '{target_user['email']}' already holds role '{new_role}'.",
        )

    # 5. Execute atomic role change and audit log entry
    audit_record = update_user_role_with_audit(
        target_user_id=user_id,
        actor_user_id=actor_id,
        new_role=new_role,
        reason=req.reason,
    )

    if not audit_record:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update role in database.",
        )

    log.info(
        f"Admin {current_admin['email']} changed user {target_user['email']} role: {old_role} -> {new_role}",
        extra={"component": "ADMIN_ROLE"}
    )

    return RoleUpdateResponse(
        success=True,
        audit_id=audit_record["audit_id"],
        target_user_id=user_id,
        old_role=old_role,
        new_role=new_role,
        reason=req.reason,
        updated_at=audit_record["created_at"],
    )


# ── GET /api/admin/role-history ───────────────────────────────────────────────
@router.get("/role-history", response_model=RoleAuditListResponse)
async def get_role_history(
    target_user_id: Optional[str] = Query(None, description="Optional target user ID filter"),
    limit: int = Query(50, ge=1, le=100, description="Page limit"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    current_admin: Dict[str, Any] = Depends(require_admin),
):
    """
    Fetch chronological audit history of all role modifications.
    Includes target and actor identification, old/new roles, timestamps, and reasons.
    """
    total = count_role_audits(target_user_id=target_user_id)
    records = get_role_audit_history(limit=limit, offset=offset, target_user_id=target_user_id)
    return RoleAuditListResponse(
        total=total,
        items=[RoleAuditItem(**r) for r in records],
        limit=limit,
        offset=offset,
    )
