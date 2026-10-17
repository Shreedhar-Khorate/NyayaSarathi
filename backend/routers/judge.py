"""
NyayaSarathi Judge Router
Judicial dashboard endpoints for authorized case and activity intelligence.
Protected by server-side JUDGE and ADMIN authorization.
Enforces strict privacy boundaries to prevent exposing private user research.
"""

from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, Query, HTTPException, status

from logger import get_logger
from services.auth_dependencies import require_judge_or_admin
from schemas.dashboard import (
    JudgeMetricsResponse,
    JudgeActivityListResponse,
    JudgeActivityItem,
    JudgeCaseListResponse,
    JudgeAssignedCaseItem,
    PrecedentListResponse,
    PrecedentItem,
    UpdateCaseStatusRequest,
)
from services.user_repository import (
    get_user_activities,
    get_judge_case_assignments,
    count_judge_case_assignments,
    get_case_assignment_by_id,
    update_case_assignment_status,
    get_db_connection,
    is_postgres_authoritative,
    get_pg_connection,
)

log = get_logger("nyayasarathi.judge_router")

router = APIRouter()


# ── GET /api/judge/dashboard ──────────────────────────────────────────────────
@router.get("/dashboard", response_model=JudgeMetricsResponse)
async def get_judge_dashboard(
    current_judge: Dict[str, Any] = Depends(require_judge_or_admin)
):
    """
    Overview metrics for the judicial bench.
    Uses real persistent counts:
      - assigned_matters_count: Actual matters assigned to this judge in judge_case_assignments
      - accessible_precedents: Count of High Court & Supreme Court precedents in judgments
      - recent_research_activities: Scoped strictly to the judge's own chamber activities
    """
    judge_id = current_judge["id"]

    # 1. Real assigned matters count
    assigned_count = count_judge_case_assignments(judge_id=judge_id)
    active_count = count_judge_case_assignments(judge_id=judge_id, status="ASSIGNED") + \
                   count_judge_case_assignments(judge_id=judge_id, status="IN_REVIEW") + \
                   count_judge_case_assignments(judge_id=judge_id, status="HEARING_SCHEDULED")

    # 2. Precedent counts
    precedents_count = 0
    if is_postgres_authoritative():
        try:
            conn = get_pg_connection()
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM public.judgments")
                precedents_count = cur.fetchone()[0]
            conn.close()
        except Exception:
            precedents_count = 0
    else:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("SELECT COUNT(*) FROM judgments")
                precedents_count = cursor.fetchone()[0]
            except Exception:
                precedents_count = 0

    # 3. Judge's own activity count
    if is_postgres_authoritative():
        conn = get_pg_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM public.user_activity_history WHERE user_id = %s", (judge_id,))
                judge_activities_count = cur.fetchone()[0]
        finally:
            conn.close()
    else:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM user_activity_history WHERE user_id = ?", (judge_id,))
            judge_activities_count = cursor.fetchone()[0]

    jurisdiction = current_judge.get("organization") or "High Court of Judicature"
    bench = current_judge.get("designation") or "Presiding Judicial Bench"

    return JudgeMetricsResponse(
        accessible_precedents=precedents_count,
        assigned_matters_count=assigned_count,
        active_matters_count=active_count,
        recent_research_activities=judge_activities_count,
        court_jurisdiction=jurisdiction,
        judge_name=current_judge.get("full_name") or "Hon'ble Justice",
        bench_designation=bench,
    )


# ── GET /api/judge/activity ───────────────────────────────────────────────────
@router.get("/activity", response_model=JudgeActivityListResponse)
async def get_judge_activity(
    activity_type: Optional[str] = Query(None, description="Filter: LEGAL_RESEARCH, DOCUMENT_UPLOAD, OCR_ANALYSIS, PREDICTION"),
    limit: int = Query(50, ge=1, le=100, description="Page limit"),
    offset: int = Query(0, ge=0, description="Offset index"),
    current_judge: Dict[str, Any] = Depends(require_judge_or_admin),
):
    """
    Retrieve filterable activity feed scoped strictly to the judge's authorized session.
    Privacy protection: Does NOT expose general public users' confidential legal research.
    """
    judge_id = current_judge["id"]
    activities = get_user_activities(
        user_id=judge_id,
        activity_type=activity_type,
        limit=limit,
        offset=offset,
    )

    if is_postgres_authoritative():
        conn = get_pg_connection()
        try:
            with conn.cursor() as cur:
                query = "SELECT COUNT(*) FROM public.user_activity_history WHERE user_id = %s"
                params = [judge_id]
                if activity_type:
                    query += " AND activity_type = %s"
                    params.append(activity_type)
                cur.execute(query, tuple(params))
                total = cur.fetchone()[0]
        finally:
            conn.close()
    else:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            if activity_type:
                cursor.execute(
                    "SELECT COUNT(*) FROM user_activity_history WHERE user_id = ? AND activity_type = ?",
                    (judge_id, activity_type)
                )
            else:
                cursor.execute(
                    "SELECT COUNT(*) FROM user_activity_history WHERE user_id = ?",
                    (judge_id,)
                )
            total = cursor.fetchone()[0]

    return JudgeActivityListResponse(
        total=total,
        items=[JudgeActivityItem(**a) for a in activities],
        limit=limit,
        offset=offset,
    )


# ── GET /api/judge/cases ──────────────────────────────────────────────────────
@router.get("/cases", response_model=JudgeCaseListResponse)
async def get_judge_cases(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter: ASSIGNED, IN_REVIEW, HEARING_SCHEDULED, RESERVED, DISPOSED"),
    priority: Optional[str] = Query(None, description="Filter: URGENT, REGULAR, EXPEDITED"),
    limit: int = Query(50, ge=1, le=100, description="Page limit"),
    offset: int = Query(0, ge=0, description="Offset index"),
    current_judge: Dict[str, Any] = Depends(require_judge_or_admin),
):
    """
    Fetch persistent litigation matters assigned specifically to the logged-in judge.
    Enforces authorization: Judges can only view cases explicitly assigned to their bench.
    """
    judge_id = current_judge["id"]
    cases = get_judge_case_assignments(
        judge_id=judge_id,
        status=status_filter,
        priority=priority,
        limit=limit,
        offset=offset,
    )
    total = count_judge_case_assignments(judge_id=judge_id, status=status_filter)

    return JudgeCaseListResponse(
        total=total,
        items=[JudgeAssignedCaseItem(**c) for c in cases],
        limit=limit,
        offset=offset,
        notice="Active court matters assigned to your presiding bench docket.",
    )


# ── PATCH /api/judge/cases/{case_id} ──────────────────────────────────────────
@router.patch("/cases/{case_id}", response_model=JudgeAssignedCaseItem)
async def update_assigned_case(
    case_id: str,
    req: UpdateCaseStatusRequest,
    current_judge: Dict[str, Any] = Depends(require_judge_or_admin),
):
    """
    Presiding judge updates docket progress status, hearing schedule, or judicial notes.
    Authorization: Judge must be the assigned judge for this case (or System Admin).
    """
    case = get_case_assignment_by_id(case_id)
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case assignment with ID '{case_id}' not found.",
        )

    # Scoping check: Ensure judge owns the assignment unless admin
    if current_judge.get("role") != "ADMIN" and case["judge_id"] != current_judge["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You are not authorized to modify cases assigned to another judicial bench.",
        )

    updated = update_case_assignment_status(
        assignment_id=case_id,
        status=req.status,
        notes=req.notes,
        hearing_date=req.hearing_date,
    )
    return JudgeAssignedCaseItem(**updated)


# ── GET /api/judge/precedents ─────────────────────────────────────────────────
@router.get("/precedents", response_model=PrecedentListResponse)
async def get_judge_precedents(
    search: Optional[str] = Query(None, description="Search keyword for judgment title, court, or legal query"),
    year: Optional[int] = Query(None, description="Filter by decision year"),
    limit: int = Query(50, ge=1, le=100, description="Page limit"),
    offset: int = Query(0, ge=0, description="Offset index"),
    current_judge: Dict[str, Any] = Depends(require_judge_or_admin),
):
    """
    Search and explore the public High Court & Supreme Court Legal Precedents library.
    Clearly decoupled from persistent court docket assignments.
    """
    clauses = []
    params = []

    if search and search.strip():
        term = f"%{search.strip()}%"
        clauses.append("(LOWER(title) LIKE LOWER(?) OR LOWER(parsed_court_name) LIKE LOWER(?))")
        params.extend([term, term])

    if year:
        clauses.append("year = ?")
        params.append(year)

    where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""

    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(f"SELECT COUNT(*) FROM judgments {where_sql}", tuple(params))
            total = cursor.fetchone()[0]

            query = f"""
                SELECT 
                    cnr, title, parsed_court_name AS court, year, decision_date,
                    disposal_nature_normalized AS disposal_nature, judge,
                    parsed_case_type AS case_type, parsed_petitioner AS petitioner,
                    parsed_respondent AS respondent
                FROM judgments
                {where_sql}
                ORDER BY year DESC, decision_date DESC
                LIMIT ? OFFSET ?
            """
            params.extend([limit, offset])
            cursor.execute(query, tuple(params))
            rows = [dict(r) for r in cursor.fetchall()]
        except Exception as e:
            log.warning(f"Failed to query precedents: {e}", extra={"component": "JUDGE_ROUTER"})
            total = 0
            rows = []

    items = [
        PrecedentItem(
            cnr=r.get("cnr") or "N/A",
            title=r.get("title") or "Precedent Judgment",
            court=r.get("court"),
            year=r.get("year"),
            decision_date=r.get("decision_date"),
            disposal_nature=r.get("disposal_nature"),
            judge=r.get("judge"),
            case_type=r.get("case_type"),
            petitioner=r.get("petitioner"),
            respondent=r.get("respondent"),
        )
        for r in rows
    ]

    return PrecedentListResponse(
        total=total,
        items=items,
        limit=limit,
        offset=offset,
        notice="Public Legal Precedents & Judgments Repository (Searchable historical case law).",
    )
