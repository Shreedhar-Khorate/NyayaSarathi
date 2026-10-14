"""
NyayaSarathi Google OAuth 2.0 Router.
Endpoints:
  - GET /api/auth/google          -> Redirect user to Google OAuth consent screen
  - GET /api/auth/google/callback -> Handle Google callback, upsert user, issue JWT, redirect to frontend
"""

import os
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional

import httpx
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import RedirectResponse

from logger import get_logger
from services.user_repository import get_user_by_email, create_user
from services.supabase_client import get_supabase_client
from services.auth_service import create_access_token, hash_password

load_dotenv()

log = get_logger("nyayasarathi.google_oauth")
router = APIRouter()

# ── OAuth Configuration (read from .env) ─────────────────────────────────────
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
FRONTEND_BASE_URL = os.getenv("FRONTEND_BASE_URL", "http://localhost:3000")

# This must exactly match the Authorized redirect URI set in Google Cloud Console
GOOGLE_REDIRECT_URI = os.getenv(
    "GOOGLE_REDIRECT_URI",
    "http://localhost:8000/api/auth/google/callback"
)

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"

SCOPE = "openid email profile"


@router.get("", summary="Initiate Google OAuth 2.0 Login / Signup")
def google_auth_redirect():
    """
    Redirects the user to Google's OAuth 2.0 consent screen.
    Works for both login and signup flows.
    """
    if not GOOGLE_CLIENT_ID or "your-google-client-id" in GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Google OAuth is not configured. Add GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET to backend/.env"
        )

    google_url = (
        f"{GOOGLE_AUTH_URL}"
        f"?client_id={GOOGLE_CLIENT_ID}"
        f"&redirect_uri={GOOGLE_REDIRECT_URI}"
        f"&response_type=code"
        f"&scope={SCOPE.replace(' ', '+')}"
        f"&access_type=offline"
        f"&prompt=select_account"
    )
    log.info("Redirecting user to Google OAuth consent screen.", extra={"component": "GOOGLE_OAUTH"})
    return RedirectResponse(url=google_url)


@router.get("/callback", summary="Google OAuth 2.0 Callback Handler")
async def google_auth_callback(code: Optional[str] = None, error: Optional[str] = None):
    """
    Handles Google OAuth callback:
    1. Exchanges authorization code for access token.
    2. Fetches user profile from Google (name, email, picture).
    3. Upserts user into Supabase + local SQLite.
    4. Issues a NyayaSarathi JWT token.
    5. Redirects to frontend with token in URL fragment.
    """
    if error:
        log.warning(f"Google OAuth error: {error}", extra={"component": "GOOGLE_OAUTH"})
        return RedirectResponse(
            url=f"{FRONTEND_BASE_URL}/login?error=google_auth_cancelled"
        )

    if not code:
        return RedirectResponse(
            url=f"{FRONTEND_BASE_URL}/login?error=missing_code"
        )

    # 1. Exchange code for tokens
    async with httpx.AsyncClient() as client:
        token_res = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "redirect_uri": GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
        )

    if token_res.status_code != 200:
        log.error(f"Failed to exchange Google code for token: {token_res.text}", extra={"component": "GOOGLE_OAUTH"})
        return RedirectResponse(
            url=f"{FRONTEND_BASE_URL}/login?error=token_exchange_failed"
        )

    token_data = token_res.json()
    google_access_token = token_data.get("access_token")

    # 2. Fetch user profile from Google
    async with httpx.AsyncClient() as client:
        profile_res = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {google_access_token}"},
        )

    if profile_res.status_code != 200:
        log.error(f"Failed to fetch Google profile: {profile_res.text}", extra={"component": "GOOGLE_OAUTH"})
        return RedirectResponse(
            url=f"{FRONTEND_BASE_URL}/login?error=profile_fetch_failed"
        )

    google_profile = profile_res.json()
    google_email: str = google_profile.get("email", "").strip().lower()
    google_name: str = google_profile.get("name", "").strip() or google_email.split("@")[0]
    google_sub: str = google_profile.get("sub", "")  # Google's unique user ID

    if not google_email:
        log.warning("Google profile missing email.", extra={"component": "GOOGLE_OAUTH"})
        return RedirectResponse(
            url=f"{FRONTEND_BASE_URL}/login?error=no_email"
        )

    # 3. Upsert user — find or create
    existing_user = get_user_by_email(google_email)

    if existing_user:
        # User already exists — log them in
        user = existing_user
        log.info(f"Google OAuth: existing user signed in: {google_email}", extra={"component": "GOOGLE_OAUTH"})
    else:
        # New user — create account with role USER
        # Use a random strong password (account is Google-managed, password login not applicable)
        dummy_hash = hash_password(f"google_oauth_{google_sub}_{uuid.uuid4().hex}")
        user = create_user(
            email=google_email,
            password_hash=dummy_hash,
            full_name=google_name,
            role="USER",
        )

        # Also upsert into Supabase directly for resiliency
        supabase = get_supabase_client()
        if supabase:
            try:
                supabase.table("users").upsert({
                    "id": user["id"],
                    "email": google_email,
                    "password_hash": dummy_hash,
                    "full_name": google_name,
                    "role": "USER",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }).execute()
            except Exception as e:
                log.warning(f"Supabase upsert failed for Google user: {e}", extra={"component": "GOOGLE_OAUTH"})

        log.info(f"Google OAuth: new user registered: {google_email}", extra={"component": "GOOGLE_OAUTH"})

    # 4. Issue NyayaSarathi JWT
    jwt_token = create_access_token(
        user_id=user["id"],
        email=user["email"],
        role=user.get("role", "USER"),
        full_name=user.get("full_name", google_name),
    )

    # 5. Redirect to frontend with token & user info as URL query params
    # Frontend will read this and store in localStorage
    import urllib.parse
    user_param = urllib.parse.quote_plus(user.get("full_name", ""))
    role_param = user.get("role", "USER")

    redirect_url = (
        f"{FRONTEND_BASE_URL}/login"
        f"?google_token={jwt_token}"
        f"&google_user_email={urllib.parse.quote_plus(user['email'])}"
        f"&google_user_name={user_param}"
        f"&google_user_role={role_param}"
        f"&google_user_id={user['id']}"
    )
    log.info(f"Google OAuth complete. Redirecting to frontend for: {google_email}", extra={"component": "GOOGLE_OAUTH"})
    return RedirectResponse(url=redirect_url)
