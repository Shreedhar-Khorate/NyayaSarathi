"""
Pydantic Schemas for NyayaSarathi Admin, Judge, and Advocate Dashboards.
Typed request and response models enforcing bounded pagination, role transitions,
case docketing, judicial appointment, and strict access boundaries.
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


# ── Admin Schemas ─────────────────────────────────────────────────────────────

class RoleAuditItem(BaseModel):
    """Audit log item for user role change with immutable identity snapshots."""
    id: str
    target_user_id: Optional[str] = None
    actor_user_id: Optional[str] = None
    old_role: str
    new_role: str
    reason: Optional[str] = None
    created_at: str
    target_name: Optional[str] = None
    target_email: Optional[str] = None
    actor_name: Optional[str] = None
    actor_email: Optional[str] = None


class RoleAuditListResponse(BaseModel):
    """Paginated list of role change audit logs."""
    total: int
    items: List[RoleAuditItem]
    limit: int
    offset: int


class AdminMetricsResponse(BaseModel):
    """Overview metrics for judicial platform administration."""
    total_users: int
    role_counts: Dict[str, int]
    recent_users: List[Dict[str, Any]]
    recent_role_changes: List[RoleAuditItem]
    total_activities: int
    total_judgments: int


class AdminUserItem(BaseModel):
    """Sanitized user record for administrator management (no secrets/passwords)."""
    id: str
    email: str
    full_name: str
    role: str
    avatar_url: Optional[str] = None
    organization: Optional[str] = None
    designation: Optional[str] = None
    profile_completed: bool = False
    created_at: str
    updated_at: Optional[str] = None


class AdminUserListResponse(BaseModel):
    """Paginated user list response."""
    total: int
    items: List[AdminUserItem]
    limit: int
    offset: int


class RoleUpdateRequest(BaseModel):
    """Payload to mutate an eligible user's role."""
    new_role: str = Field(..., description="Eligible role: USER, JUDGE, or ADVOCATE")
    reason: Optional[str] = Field(None, max_length=500, description="Required or optional reason for change")


class RoleUpdateResponse(BaseModel):
    """Confirmation response after successful role transition."""
    success: bool
    audit_id: str
    target_user_id: str
    old_role: str
    new_role: str
    reason: Optional[str] = None
    updated_at: str


class AssignCaseRequest(BaseModel):
    """Admin request payload to assign a litigation matter to a designated judge."""
    case_number: str = Field(..., min_length=3, max_length=100, description="Court case or docket number")
    title: str = Field(..., min_length=3, max_length=255, description="Case title / parties involved")
    court_name: str = Field(..., min_length=2, max_length=150, description="Court or Bench name")
    judge_id: str = Field(..., description="User ID of verified judge holding the JUDGE role")
    case_type: str = Field("Criminal", description="Matter category (e.g., Criminal, Bail Application, Civil)")
    priority: str = Field("REGULAR", description="REGULAR, URGENT, EXPEDITED")
    filing_date: Optional[str] = None
    hearing_date: Optional[str] = None
    petitioner: Optional[str] = None
    respondent: Optional[str] = None
    notes: Optional[str] = None


class UpdateCaseStatusRequest(BaseModel):
    """Request payload to update status or judicial notes on an assigned matter."""
    status: str = Field(..., description="ASSIGNED, IN_REVIEW, HEARING_SCHEDULED, RESERVED, DISPOSED")
    notes: Optional[str] = None
    hearing_date: Optional[str] = None


# ── Judge Schemas ─────────────────────────────────────────────────────────────

class JudgeMetricsResponse(BaseModel):
    """KPI metrics for the authorized judge dashboard."""
    accessible_precedents: int = Field(..., description="Indexed High Court and Supreme Court precedent repository")
    assigned_matters_count: int = Field(..., description="Persistent court matters assigned to this judge's bench")
    active_matters_count: int = Field(0, description="Active assigned matters excluding disposed cases")
    recent_research_activities: int = Field(..., description="Permitted activities from judge's own chamber session")
    court_jurisdiction: str
    judge_name: str
    bench_designation: str


class JudgeActivityItem(BaseModel):
    """Judicial activity log item scoped to current judge."""
    id: str
    activity_type: str
    title: str
    query_text: Optional[str] = None
    resource_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: str


class JudgeActivityListResponse(BaseModel):
    """Paginated judicial activities scoped to current judge."""
    total: int
    items: List[JudgeActivityItem]
    limit: int
    offset: int


class JudgeAssignedCaseItem(BaseModel):
    """Persistent litigation matter assigned to a presiding judge."""
    id: str
    case_number: str
    title: str
    court_name: str
    case_type: str
    judge_id: str
    assigned_by_id: Optional[str] = None
    status: str
    priority: str
    filing_date: Optional[str] = None
    hearing_date: Optional[str] = None
    petitioner: Optional[str] = None
    respondent: Optional[str] = None
    notes: Optional[str] = None
    created_at: str
    updated_at: str


class JudgeCaseListResponse(BaseModel):
    """Paginated list of persistent litigation matters assigned to the judge."""
    total: int
    items: List[JudgeAssignedCaseItem]
    limit: int
    offset: int
    notice: Optional[str] = None


class PrecedentItem(BaseModel):
    """Public High Court or Supreme Court legal precedent from judgments repository."""
    cnr: str
    title: str
    court: Optional[str] = None
    year: Optional[int] = None
    decision_date: Optional[str] = None
    disposal_nature: Optional[str] = None
    judge: Optional[str] = None
    case_type: Optional[str] = None
    petitioner: Optional[str] = None
    respondent: Optional[str] = None


class PrecedentListResponse(BaseModel):
    """Searchable public legal precedents repository."""
    total: int
    items: List[PrecedentItem]
    limit: int
    offset: int
    notice: Optional[str] = None


# ── Advocate Schemas ──────────────────────────────────────────────────────────

class AdvocateMetricsResponse(BaseModel):
    """KPI overview metrics for the Advocate portal dashboard."""
    advocate_name: str
    organization: str
    designation: str
    total_activities: int = Field(..., description="Total platform activities by this advocate")
    legal_research_count: int = Field(0, description="Legal research queries executed")
    drafts_created: int = Field(0, description="Legal documents drafted")
    documents_analysed: int = Field(0, description="Documents uploaded or OCR-analysed")
    predictions_run: int = Field(0, description="Judgment prediction queries run")


class AdvocateActivityItem(BaseModel):
    """Single advocate activity record scoped to the requesting user."""
    id: str
    activity_type: str
    title: str
    query_text: Optional[str] = None
    resource_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: str


class AdvocateActivityListResponse(BaseModel):
    """Paginated personal activity list for the requesting advocate."""
    total: int
    items: List[AdvocateActivityItem]
    limit: int
    offset: int


class JudgePromoteRequest(BaseModel):
    """Judge-only request payload to nominate a USER or ADVOCATE to the JUDGE role."""
    target_user_id: str = Field(..., description="User ID of the person to be appointed as Judge")
    reason: Optional[str] = Field(
        None,
        max_length=500,
        description="Judicial appointment reason / nomination note",
    )
