"""
NyayaSarathi Supabase Client Helper.
Provides access to Supabase PostgreSQL database, Storage, and Auth using the
official Python client (supabase-py).
"""

import os
import logging
from typing import Optional
from dotenv import load_dotenv

# Always load backend .env variables dynamically
load_dotenv()

logger = logging.getLogger("nyayasarathi.supabase")

_supabase_client = None


def normalize_supabase_url(url: str) -> str:
    """Strips trailing slashes and common subpaths like /rest/v1 to get clean base URL."""
    clean = url.strip().rstrip("/")
    if clean.endswith("/rest/v1"):
        clean = clean[:-len("/rest/v1")].rstrip("/")
    return clean


def get_supabase_client():
    """
    Returns an initialized Supabase Client if SUPABASE_URL and
    SUPABASE_SERVICE_ROLE_KEY (or SUPABASE_ANON_KEY) are configured in .env.

    Returns None if Supabase is not configured or if `supabase` package is not installed.
    """
    global _supabase_client

    if _supabase_client is not None:
        return _supabase_client

    raw_url = os.getenv("SUPABASE_URL")
    # Prefer service_role key for backend operations (bypasses RLS), fallback to anon key
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")

    if not raw_url or not supabase_key:
        logger.debug("Supabase credentials not fully configured in environment.")
        return None

    # Ignore placeholder default values
    if "your-project-ref" in raw_url or "your-supabase" in supabase_key:
        logger.debug("Supabase credentials contain default placeholders.")
        return None

    supabase_url = normalize_supabase_url(raw_url)

    try:
        from supabase import create_client, Client
        _supabase_client = create_client(supabase_url, supabase_key)
        logger.info(f"Supabase client initialized successfully for {supabase_url}")
        return _supabase_client
    except ImportError:
        logger.warning(
            "The 'supabase' Python package is not installed. "
            "Run 'pip install supabase' to enable Supabase integration."
        )
        return None
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {e}")
        return None


def is_supabase_configured() -> bool:
    """Returns True if valid Supabase environment variables are present in .env."""
    raw_url = os.getenv("SUPABASE_URL", "")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "") or os.getenv("SUPABASE_ANON_KEY", "")
    return bool(raw_url and key and "your-project-ref" not in raw_url and "your-supabase" not in key)
