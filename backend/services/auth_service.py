"""
NyayaSarathi Authentication & JWT Service
Provides password hashing via direct bcrypt and JWT token encoding/decoding.
Configured with Supabase-compatible JWT claim structures.
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import jwt
import bcrypt

from logger import get_logger

log = get_logger("nyayasarathi.auth_service")

# JWT Configuration
# Require JWT_SECRET_KEY from environment. For test suites/local dev without .env, generate an ephemeral runtime secret.
_configured_jwt_secret = os.getenv("JWT_SECRET_KEY", "").strip()
if not _configured_jwt_secret:
    import secrets
    _configured_jwt_secret = os.environ.get("NYAYASARATHI_EPHEMERAL_JWT_SECRET") or secrets.token_hex(32)
    os.environ["NYAYASARATHI_EPHEMERAL_JWT_SECRET"] = _configured_jwt_secret

JWT_SECRET_KEY = _configured_jwt_secret
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 7


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    pw_bytes = password.encode("utf-8")[:72]  # Truncate to bcrypt 72-byte max limit
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pw_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plaintext password against bcrypt hash."""
    try:
        pw_bytes = plain_password.encode("utf-8")[:72]
        hash_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(pw_bytes, hash_bytes)
    except Exception as err:
        log.warning(f"Password verification error: {err}", extra={"component": "AUTH"})
        return False


def create_access_token(
    user_id: str,
    email: str,
    role: str = "ADVOCATE",
    full_name: str = "",
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a signed JWT access token.
    Follows standard claims compatible with Supabase Auth (`sub`, `email`, `role`, `aud`, `exp`).
    """
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)

    payload: Dict[str, Any] = {
        "sub": user_id,  # Standard Subject identifier (user UUID)
        "email": email,
        "role": role,
        "name": full_name,
        "aud": "authenticated",
        "iss": "nyayasarathi",
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }

    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return token


def decode_access_token(token: str) -> Dict[str, Any]:
    """
    Decode and verify a JWT access token.
    Raises PyJWT exceptions (ExpiredSignatureError, InvalidTokenError) if invalid.
    """
    payload = jwt.decode(
        token,
        JWT_SECRET_KEY,
        algorithms=[JWT_ALGORITHM],
        options={"verify_aud": False}
    )
    return payload
