"""
NyayaSarathi Authorization & Role Dependencies
Enforces backend authorization boundaries for protected API endpoints.
Ensures current role is always evaluated against the database to block stale JWT claims.
"""

from typing import Optional, Dict, Any, List, Callable
from fastapi import HTTPException, Depends, Header, status
from fastapi.security import OAuth2PasswordBearer
import jwt

from services.auth_service import decode_access_token
from services.user_repository import get_user_by_id

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    authorization: Optional[str] = Header(None)
) -> Dict[str, Any]:
    """
    FastAPI dependency to extract and verify JWT from Bearer header.
    Validates user state directly against the database on each call, ensuring
    demoted or deactivated users lose elevated access immediately.
    """
    raw_token = token
    if not raw_token and authorization and authorization.startswith("Bearer "):
        raw_token = authorization.split(" ")[1]

    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token is missing.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_access_token(raw_token)
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Database check ensures freshest role and prevents stale JWT escalation
        user = get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account no longer exists.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session token has expired. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )


def require_role(allowed_roles: List[str]) -> Callable:
    """Factory creating a role-enforcement dependency."""
    async def _role_checker(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        user_role = current_user.get("role", "USER").upper()
        normalized_allowed = [r.upper() for r in allowed_roles]
        if user_role not in normalized_allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: Requires role in {allowed_roles}. Current role: {user_role}",
            )
        return current_user
    return _role_checker


# Convenient pre-configured role dependencies
require_admin = require_role(["ADMIN"])
require_judge = require_role(["JUDGE"])
require_judge_or_admin = require_role(["JUDGE", "ADMIN"])
require_advocate = require_role(["ADVOCATE"])
require_advocate_or_admin = require_role(["ADVOCATE", "ADMIN"])
