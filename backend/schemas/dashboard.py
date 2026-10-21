"""
Pydantic Schemas for NyayaSarathi Admin and Advocate Dashboards.
Typed request and response models enforcing bounded pagination, role transitions,
and strict access boundaries. Supported active roles: USER, ADVOCATE, ADMIN.
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
    new_role: str = Field(..., description="Eligible role: USER, ADVOCATE, or ADMIN")
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
