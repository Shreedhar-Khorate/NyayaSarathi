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
from services.user_repository import (
    get_user_by_email,
    get_user_by_id,
    get_user_by_google_sub,
    create_user,
    update_user_profile,
)
from services.supabase_client import get_supabase_client
from services.auth_service import create_access_token, hash_password

load_dotenv()

log = get_logger("nyayasarathi.google_oauth")
router = APIRouter()

# ── OAuth Configuration Helpers ──────────────────────────────────────────────
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"

SCOPE = "openid email profile"


def get_google_config(request: Request):
    """
    Dynamically determines Google OAuth configuration and redirect targets:
    - In production (Render) or non-localhost requests:
      defaults redirect_uri to 'https://nyayasarathi.onrender.com/api/auth/google/callback'
      and frontend_base to 'https://nyayasarathi.vercel.app'.
    - In local development:
      defaults redirect_uri to 'http://localhost:8000/api/auth/google/callback'
      and frontend_base to 'http://localhost:3000'.
    - Can be explicitly overridden via GOOGLE_REDIRECT_URI and FRONTEND_BASE_URL.
    """
    client_id = os.getenv("GOOGLE_CLIENT_ID", "").strip()
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET", "").strip()
    is_prod = os.getenv("ENVIRONMENT", "").strip().lower() == "production"

    host = (request.headers.get("x-forwarded-host") or request.headers.get("host") or "").lower()
    is_local_host = any(h in host for h in ("localhost", "127.0.0.1", "0.0.0.0", "testserver")) or not host
    is_production_request = is_prod or (host and not is_local_host)

    # 1. Resolve redirect URI
    configured_redirect = os.getenv("GOOGLE_REDIRECT_URI", "").strip()
    if is_production_request:
        if configured_redirect and "localhost" not in configured_redirect and "127.0.0.1" not in configured_redirect:
            redirect_uri = configured_redirect
        else:
            redirect_uri = "https://nyayasarathi.onrender.com/api/auth/google/callback"
    else:
        if configured_redirect:
            redirect_uri = configured_redirect
        else:
            proto = request.headers.get("x-forwarded-proto", request.url.scheme)
            redirect_uri = f"{proto}://{host or 'localhost:8000'}/api/auth/google/callback"

    # 2. Resolve frontend base URL
    configured_frontend = os.getenv("FRONTEND_BASE_URL", "").strip()
    if is_production_request:
        # In production, NEVER redirect to localhost!
        if configured_frontend and "localhost" not in configured_frontend and "127.0.0.1" not in configured_frontend:
            frontend_base = configured_frontend.rstrip("/")
        else:
            frontend_base = "https://nyayasarathi.vercel.app"
    else:
        if configured_frontend:
            frontend_base = configured_frontend.rstrip("/")
        else:
            frontend_base = "http://localhost:3000"

    return client_id, client_secret, redirect_uri, frontend_base


@router.get("", summary="Initiate Google OAuth 2.0 Login / Signup")
def google_auth_redirect(request: Request):
    """
    Redirects the user to Google's OAuth 2.0 consent screen.
    Works for both login and signup flows.
    """
    client_id, _, redirect_uri, _ = get_google_config(request)
    if not client_id or "your-google-client-id" in client_id:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Google OAuth is not configured. Add GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET to backend/.env"
        )

    google_url = (
        f"{GOOGLE_AUTH_URL}"
        f"?client_id={client_id}"
        f"&redirect_uri={redirect_uri}"
        f"&response_type=code"
        f"&scope={SCOPE.replace(' ', '+')}"
        f"&access_type=offline"
        f"&prompt=select_account"
    )
    log.info(f"Redirecting user to Google OAuth consent screen with redirect_uri: {redirect_uri}", extra={"component": "GOOGLE_OAUTH"})
    return RedirectResponse(url=google_url)


@router.get("/callback", summary="Google OAuth 2.0 Callback Handler")
async def google_auth_callback(
    request: Request,
    code: Optional[str] = None,
    error: Optional[str] = None
):
    """
    Handles Google OAuth callback:
    1. Exchanges authorization code for access token.
    2. Fetches user profile from Google (name, email, picture).
    3. Upserts user into Supabase + local SQLite.
    4. Issues a NyayaSarathi JWT token.
    5. Redirects to frontend with token in URL query params.
    """
    client_id, client_secret, redirect_uri, frontend_base = get_google_config(request)

    if error:
        log.warning(f"Google OAuth error: {error}", extra={"component": "GOOGLE_OAUTH"})
        return RedirectResponse(
            url=f"{frontend_base}/login?error=google_auth_cancelled"
        )

    if not code:
        return RedirectResponse(
            url=f"{frontend_base}/login?error=missing_code"
        )

    # 1. Exchange code for tokens
    async with httpx.AsyncClient() as client:
        token_res = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
        )

    if token_res.status_code != 200:
        log.error(f"Failed to exchange Google code for token: {token_res.text}", extra={"component": "GOOGLE_OAUTH"})
        return RedirectResponse(
            url=f"{frontend_base}/login?error=token_exchange_failed"
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
            url=f"{frontend_base}/login?error=profile_fetch_failed"
        )

    google_profile = profile_res.json()
    google_email: str = google_profile.get("email", "").strip().lower()
    google_name: str = google_profile.get("name", "").strip() or google_email.split("@")[0]
    google_sub: str = google_profile.get("sub", "")  # Google's unique user ID

    google_avatar: Optional[str] = google_profile.get("picture")

    # 3. Upsert user — match by google_sub first, then verified email
    user = None
    if google_sub:
        user = get_user_by_google_sub(google_sub)

    if not user:
        user = get_user_by_email(google_email)
        if user and google_sub and not user.get("google_sub"):
            # Link existing account with verified Google identity
            update_user_profile(user["id"], google_sub=google_sub, avatar_url=google_avatar or user.get("avatar_url"))
            user = get_user_by_id(user["id"])

    if user:
        log.info(f"Google OAuth: existing user signed in: {google_email}", extra={"component": "GOOGLE_OAUTH"})
        # Update avatar if missing
        if google_avatar and not user.get("avatar_url"):
            update_user_profile(user["id"], avatar_url=google_avatar)
            user = get_user_by_id(user["id"])
    else:
        # New Google user — created with password_hash=None and safe default role 'USER'
        user = create_user(
            email=google_email,
            password_hash=None,
            full_name=google_name,
            role="USER",
            avatar_url=google_avatar,
            google_sub=google_sub,
            profile_completed=False,
        )
        log.info(f"Google OAuth: new user registered: {google_email}", extra={"component": "GOOGLE_OAUTH"})

    # 4. Issue NyayaSarathi JWT
    jwt_token = create_access_token(
        user_id=user["id"],
        email=user["email"],
        role=user.get("role", "USER"),
        full_name=user.get("full_name", google_name),
    )

    # 5. Redirect to frontend with token & profile data in query params
    import urllib.parse
    user_param = urllib.parse.quote_plus(user.get("full_name", ""))
    role_param = user.get("role", "USER")
    completed_param = "true" if user.get("profile_completed") else "false"

    redirect_url = (
        f"{frontend_base}/login"
        f"?google_token={jwt_token}"
        f"&google_user_email={urllib.parse.quote_plus(user['email'])}"
        f"&google_user_name={user_param}"
        f"&google_user_role={role_param}"
        f"&google_user_id={user['id']}"
        f"&google_profile_completed={completed_param}"
    )
    log.info(f"Google OAuth complete. Redirecting to frontend for: {google_email}", extra={"component": "GOOGLE_OAUTH"})
    return RedirectResponse(url=redirect_url)
