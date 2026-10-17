"""
NyayaSarathi Admin Router
Administrative endpoints for user role management, system metrics, and audit history.
Protected strictly by server-side ADMIN authorization.
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
    AssignCaseRequest,
    JudgeAssignedCaseItem,
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
    create_case_assignment,
    get_judge_case_assignments,
    count_judge_case_assignments,
    get_case_assignment_by_id,
    delete_case_assignment,
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
    role: Optional[str] = Query(None, description="Filter by role: USER, JUDGE, ADVOCATE, ADMIN"),
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
    """
    actor_id = current_admin["id"]
    new_role = req.new_role.strip().upper()
    valid_roles = {"USER", "JUDGE", "ADVOCATE", "ADMIN"}

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


# ── Case Assignment Management (Admin Operations) ─────────────────────────────

@router.post("/cases/assign", response_model=JudgeAssignedCaseItem, status_code=status.HTTP_201_CREATED)
async def assign_case_to_judge(
    req: AssignCaseRequest,
    current_admin: Dict[str, Any] = Depends(require_admin),
):
    """
    Assign a litigation matter or case docket to an eligible judicial bench.
    Validation: Target user must exist and possess the JUDGE role.
    """
    target_judge = get_user_by_id(req.judge_id)
    if not target_judge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Target judge with ID '{req.judge_id}' does not exist.",
        )

    if target_judge.get("role") != "JUDGE":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User '{target_judge['email']}' has role '{target_judge.get('role')}'. Cases may only be assigned to accounts with the 'JUDGE' role.",
        )

    assignment = create_case_assignment(
        case_number=req.case_number,
        title=req.title,
        court_name=req.court_name,
        judge_id=req.judge_id,
        assigned_by_id=current_admin["id"],
        case_type=req.case_type,
        priority=req.priority,
        filing_date=req.filing_date,
        hearing_date=req.hearing_date,
        petitioner=req.petitioner,
        respondent=req.respondent,
        notes=req.notes,
    )

    log.info(
        f"Admin {current_admin['email']} assigned case {req.case_number} to Judge {target_judge['email']}",
        extra={"component": "CASE_ASSIGNMENT"}
    )
    return JudgeAssignedCaseItem(**assignment)


@router.get("/cases", response_model=List[JudgeAssignedCaseItem])
async def list_all_case_assignments(
    judge_id: Optional[str] = Query(None, description="Optional judge ID filter"),
    status: Optional[str] = Query(None, description="Optional status filter"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_admin: Dict[str, Any] = Depends(require_admin),
):
    """List case assignments across all benches (Admin audit view)."""
    if judge_id:
        items = get_judge_case_assignments(judge_id=judge_id, status=status, limit=limit, offset=offset)
    else:
        # Query all assignments
        if is_postgres_authoritative():
            conn = get_pg_connection()
            try:
                import psycopg2.extras
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    query = "SELECT * FROM public.judge_case_assignments"
                    params = []
                    if status:
                        query += " WHERE status = %s"
                        params.append(status.strip().upper())
                    query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
                    params.extend([limit, offset])
                    cur.execute(query, tuple(params))
                    rows = cur.fetchall()
                    items = []
                    for r in rows:
                        d = dict(r)
                        for date_field in ["filing_date", "hearing_date", "created_at", "updated_at"]:
                            if hasattr(d.get(date_field), "isoformat"):
                                d[date_field] = d[date_field].isoformat()
                        items.append(d)
            finally:
                conn.close()
        else:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                query = "SELECT * FROM judge_case_assignments"
                params = []
                if status:
                    query += " WHERE status = ?"
                    params.append(status.strip().upper())
                query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
                params.extend([limit, offset])
                cursor.execute(query, tuple(params))
                items = [dict(r) for r in cursor.fetchall()]

    return [JudgeAssignedCaseItem(**i) for i in items]


@router.delete("/cases/{case_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_case_assignment(
    case_id: str,
    current_admin: Dict[str, Any] = Depends(require_admin),
):
    """Revoke or delete a case assignment."""
    case = get_case_assignment_by_id(case_id)
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case assignment with ID '{case_id}' not found.",
        )
    deleted = delete_case_assignment(case_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete case assignment.",
        )

