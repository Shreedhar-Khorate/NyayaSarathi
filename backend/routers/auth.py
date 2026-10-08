"""
NyayaSarathi Authentication Router
Endpoints:
  - POST /api/auth/signup  -> Register new user account
  - POST /api/auth/login   -> Authenticate credentials & generate JWT
  - GET  /api/auth/me      -> Fetch current authenticated user profile
"""

from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Header, status
from fastapi.security import OAuth2PasswordBearer
import jwt

from logger import get_logger
from schemas.auth import (
    SignupRequest,
    LoginRequest,
    UserProfile,
    AuthTokenResponse,
)
from services.user_repository import (
    get_user_by_email,
    get_user_by_id,
    create_user,
)
from services.auth_service import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
)

log = get_logger("nyayasarathi.auth_router")

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


# ── Dependency: Get Current Authenticated User ──────────────────────────────
async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    authorization: Optional[str] = Header(None)
) -> Dict[str, Any]:
    """
    FastAPI dependency to extract and verify JWT from Bearer header or OAuth2 scheme.
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


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/signup", response_model=AuthTokenResponse, status_code=status.HTTP_201_CREATED)
async def signup(req: SignupRequest):
    """Register a new user account and return a signed JWT token."""
    existing_user = get_user_by_email(req.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists."
        )

    hashed_pw = hash_password(req.password)
    new_user = create_user(
        email=req.email,
        password_hash=hashed_pw,
        full_name=req.full_name,
        role=req.role or "ADVOCATE"
    )

    token = create_access_token(
        user_id=new_user["id"],
        email=new_user["email"],
        role=new_user["role"],
        full_name=new_user["full_name"],
    )

    log.info(f"New user registered: {new_user['email']} ({new_user['role']})", extra={"component": "AUTH"})

    return AuthTokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserProfile(**new_user)
    )


@router.post("/login", response_model=AuthTokenResponse)
async def login(req: LoginRequest):
    """Authenticate user credentials and return a signed JWT token."""
    user = get_user_by_email(req.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email address or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not verify_password(req.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email address or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(
        user_id=user["id"],
        email=user["email"],
        role=user["role"],
        full_name=user["full_name"],
    )

    log.info(f"User logged in successfully: {user['email']}", extra={"component": "AUTH"})

    user_profile = UserProfile(
        id=user["id"],
        email=user["email"],
        full_name=user["full_name"],
        role=user["role"],
        created_at=user["created_at"],
    )

    return AuthTokenResponse(
        access_token=token,
        token_type="bearer",
        user=user_profile
    )


@router.get("/me", response_model=UserProfile)
async def get_me(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Fetch profile of the currently authenticated user."""
    return UserProfile(
        id=current_user["id"],
        email=current_user["email"],
        full_name=current_user["full_name"],
        role=current_user["role"],
        created_at=current_user["created_at"],
    )
