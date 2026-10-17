"""
Authentication & Profile Pydantic Schemas for NyayaSarathi.
Request and response data models for user registration, login, profile operations, and history.
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, EmailStr, Field


class SignupRequest(BaseModel):
    """User registration payload."""
    email: EmailStr = Field(..., description="Unique user email address")
    password: str = Field(..., min_length=6, description="Minimum 6 characters")
    full_name: str = Field(..., min_length=2, description="Full user name")
    role: Optional[str] = Field("USER", description="Safe default role: USER")


class LoginRequest(BaseModel):
    """User credentials for authentication."""
    email: EmailStr = Field(..., description="User account email")
    password: str = Field(..., description="Account password")


class UserProfile(BaseModel):
    """Authenticated user profile representation."""
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


class ProfileUpdateRequest(BaseModel):
    """Allowlisted profile fields that a user is permitted to update."""
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    avatar_url: Optional[str] = Field(None, max_length=500000)
    organization: Optional[str] = Field(None, max_length=150)
    designation: Optional[str] = Field(None, max_length=100)


class ProfileCompleteRequest(BaseModel):
    """Onboarding profile completion request for missing required fields."""
    full_name: str = Field(..., min_length=2, max_length=100, description="Full legal professional or researcher name")
    organization: str = Field(..., min_length=2, max_length=150, description="Chambers, High Court, Law Firm, or University")
    designation: str = Field(..., min_length=2, max_length=100, description="Advocate, Senior Counsel, Researcher, etc.")
    avatar_url: Optional[str] = Field(None, max_length=500000)


class AuthTokenResponse(BaseModel):
    """JWT bearer token and authenticated user payload."""
    access_token: str
    token_type: str = "bearer"
    user: UserProfile


# ── Activity History Schemas ──────────────────────────────────────────────────

class ActivityHistoryItem(BaseModel):
    """Single user activity log record."""
    id: str
    user_id: str
    activity_type: str
    title: str
    query_text: Optional[str] = None
    resource_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: str


class ActivityHistoryListResponse(BaseModel):
    """Paginated list of activity records."""
    total: int
    items: List[ActivityHistoryItem]


class ActivityCreateRequest(BaseModel):
    """Payload to record an activity."""
    activity_type: str = Field(..., description="LEGAL_RESEARCH | DOCUMENT_UPLOAD | OCR_ANALYSIS | PREDICTION")
    title: str = Field(..., min_length=2, max_length=200)
    query_text: Optional[str] = None
    resource_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


__all__ = [
    "SignupRequest",
    "LoginRequest",
    "UserProfile",
    "ProfileUpdateRequest",
    "ProfileCompleteRequest",
    "AuthTokenResponse",
    "ActivityHistoryItem",
    "ActivityHistoryListResponse",
    "ActivityCreateRequest",
]
