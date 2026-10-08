"""
Authentication Pydantic Schemas for NyayaSarathi.
Request and response data models for user registration, login, and profile operations.
"""

from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class SignupRequest(BaseModel):
    """User registration payload."""
    email: EmailStr = Field(..., description="Unique user email address")
    password: str = Field(..., min_length=6, description="Minimum 6 characters")
    full_name: str = Field(..., min_length=2, description="Full user name")
    role: Optional[str] = Field("ADVOCATE", description="ADVOCATE | RESEARCHER | JUDGE | CLIENT")


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
    created_at: str


class AuthTokenResponse(BaseModel):
    """JWT bearer token and authenticated user payload."""
    access_token: str
    token_type: str = "bearer"
    user: UserProfile


__all__ = [
    "SignupRequest",
    "LoginRequest",
    "UserProfile",
    "AuthTokenResponse",
]
