"""
NyayaSarathi User & History Repository
Decoupled Data Access Layer for User Profiles and Activity History.
Connects primarily to Supabase (PostgreSQL) with automatic fallback to local SQLite.
Enforces security, validated profile updates, role integrity, and isolated user history.
"""

import json
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

from logger import get_logger
from services.supabase_client import get_supabase_client

log = get_logger("nyayasarathi.user_repo")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "nyayasarathi.db")


def get_db_connection() -> sqlite3.Connection:
    """Get connection to local SQLite database with Row factory."""
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_user_table():
    """
    Auto-initialize the `users` and `user_activity_history` tables in SQLite.
    Schema matches PostgreSQL/Supabase conventions.
    """
    log.info("Initializing user database tables...", extra={"component": "USER_REPO"})
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT,
                full_name TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'USER',
                avatar_url TEXT,
                organization TEXT,
                designation TEXT,
                profile_completed INTEGER NOT NULL DEFAULT 0,
                google_sub TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        # Automatically migrate existing SQLite users table if columns are missing
        cursor.execute("PRAGMA table_info(users)")
        existing_cols = {row["name"] for row in cursor.fetchall()}
        if "avatar_url" not in existing_cols:
            cursor.execute("ALTER TABLE users ADD COLUMN avatar_url TEXT")
        if "organization" not in existing_cols:
            cursor.execute("ALTER TABLE users ADD COLUMN organization TEXT")
        if "designation" not in existing_cols:
            cursor.execute("ALTER TABLE users ADD COLUMN designation TEXT")
        if "profile_completed" not in existing_cols:
            cursor.execute("ALTER TABLE users ADD COLUMN profile_completed INTEGER NOT NULL DEFAULT 0")
        if "google_sub" not in existing_cols:
            cursor.execute("ALTER TABLE users ADD COLUMN google_sub TEXT")
        if "updated_at" not in existing_cols:
            cursor.execute("ALTER TABLE users ADD COLUMN updated_at TEXT NOT NULL DEFAULT ''")

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_google_sub ON users(google_sub)")

        # Create user_activity_history in SQLite
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_activity_history (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                activity_type TEXT NOT NULL,
                title TEXT NOT NULL,
                query_text TEXT,
                resource_id TEXT,
                metadata TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_activity_user_created ON user_activity_history(user_id, created_at DESC)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_activity_type ON user_activity_history(activity_type)")

        conn.commit()
    log.info("User database tables ready.", extra={"component": "USER_REPO"})


def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Retrieve user dictionary by email (case-insensitive) from Supabase or local SQLite."""
    clean_email = email.strip()

    client = get_supabase_client()
    if client:
        try:
            res = client.table("users").select("*").ilike("email", clean_email).limit(1).execute()
            if res.data:
                return dict(res.data[0])
        except Exception as e:
            log.warning(f"Supabase get_user_by_email failed: {e}. Falling back to SQLite.", extra={"component": "USER_REPO"})

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """SELECT id, email, password_hash, full_name, role, avatar_url, 
                      organization, designation, profile_completed, google_sub, 
                      created_at, updated_at 
               FROM users WHERE LOWER(email) = LOWER(?)""",
            (clean_email,)
        )
        row = cursor.fetchone()
        if row:
            d = dict(row)
            d["profile_completed"] = bool(d.get("profile_completed"))
            return d
    return None


def get_user_by_google_sub(google_sub: str) -> Optional[Dict[str, Any]]:
    """Retrieve user dictionary by verified Google Subject ID."""
    if not google_sub:
        return None

    client = get_supabase_client()
    if client:
        try:
            res = client.table("users").select("*").eq("google_sub", google_sub).limit(1).execute()
            if res.data:
                return dict(res.data[0])
        except Exception as e:
            log.warning(f"Supabase get_user_by_google_sub failed: {e}. Falling back to SQLite.", extra={"component": "USER_REPO"})

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """SELECT id, email, password_hash, full_name, role, avatar_url, 
                      organization, designation, profile_completed, google_sub, 
                      created_at, updated_at 
               FROM users WHERE google_sub = ?""",
            (google_sub,)
        )
        row = cursor.fetchone()
        if row:
            d = dict(row)
            d["profile_completed"] = bool(d.get("profile_completed"))
            return d
    return None


def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve user dictionary by ID from Supabase or local SQLite."""
    client = get_supabase_client()
    if client:
        try:
            res = client.table("users").select("*").eq("id", user_id).limit(1).execute()
            if res.data:
                return dict(res.data[0])
        except Exception as e:
            log.warning(f"Supabase get_user_by_id failed: {e}. Falling back to SQLite.", extra={"component": "USER_REPO"})

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """SELECT id, email, password_hash, full_name, role, avatar_url, 
                      organization, designation, profile_completed, google_sub, 
                      created_at, updated_at 
               FROM users WHERE id = ?""",
            (user_id,)
        )
        row = cursor.fetchone()
        if row:
            d = dict(row)
            d["profile_completed"] = bool(d.get("profile_completed"))
            return d
    return None


def create_user(
    email: str,
    password_hash: Optional[str] = None,
    full_name: str = "",
    role: str = "USER",
    avatar_url: Optional[str] = None,
    organization: Optional[str] = None,
    designation: Optional[str] = None,
    google_sub: Optional[str] = None,
    profile_completed: bool = False,
) -> Dict[str, Any]:
    """Create a new user in Supabase and sync to local SQLite."""
    user_id = str(uuid.uuid4())
    now_iso = datetime.now(timezone.utc).isoformat()
    clean_email = email.strip().lower()
    clean_name = full_name.strip()

    user_payload = {
        "id": user_id,
        "email": clean_email,
        "password_hash": password_hash,
        "full_name": clean_name,
        "role": role,
        "avatar_url": avatar_url,
        "organization": organization,
        "designation": designation,
        "profile_completed": profile_completed,
        "google_sub": google_sub,
        "created_at": now_iso,
        "updated_at": now_iso,
    }

    client = get_supabase_client()
    if client:
        try:
            client.table("users").insert(user_payload).execute()
            log.info(f"User {clean_email} created in Supabase.", extra={"component": "USER_REPO"})
        except Exception as e:
            log.warning(f"Supabase create_user failed: {e}. Writing to local SQLite.", extra={"component": "USER_REPO"})

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO users (
                id, email, password_hash, full_name, role, avatar_url,
                organization, designation, profile_completed, google_sub,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                clean_email,
                password_hash,
                clean_name,
                role,
                avatar_url,
                organization,
                designation,
                1 if profile_completed else 0,
                google_sub,
                now_iso,
                now_iso,
            ),
        )
        conn.commit()

    return user_payload


def update_user_profile(
    user_id: str,
    full_name: Optional[str] = None,
    avatar_url: Optional[str] = None,
    organization: Optional[str] = None,
    designation: Optional[str] = None,
    google_sub: Optional[str] = None,
    profile_completed: Optional[bool] = None,
) -> Optional[Dict[str, Any]]:
    """
    Safely update permitted profile fields for the authenticated user.
    NEVER allows changing id, email, password_hash, or role through profile update.
    """
    now_iso = datetime.now(timezone.utc).isoformat()
    updates: Dict[str, Any] = {"updated_at": now_iso}

    if full_name is not None and full_name.strip():
        updates["full_name"] = full_name.strip()
    if avatar_url is not None:
        updates["avatar_url"] = avatar_url.strip() if avatar_url.strip() else None
    if organization is not None:
        updates["organization"] = organization.strip()
    if designation is not None:
        updates["designation"] = designation.strip()
    if google_sub is not None:
        updates["google_sub"] = google_sub.strip()
    if profile_completed is not None:
        updates["profile_completed"] = bool(profile_completed)

    # 1. Update Supabase
    client = get_supabase_client()
    if client:
        try:
            res = client.table("users").update(updates).eq("id", user_id).execute()
            if res.data:
                log.info(f"Updated user profile {user_id} in Supabase.", extra={"component": "USER_REPO"})
        except Exception as e:
            log.warning(f"Supabase update_user_profile failed: {e}. Writing to SQLite.", extra={"component": "USER_REPO"})

    # 2. Update local SQLite
    with get_db_connection() as conn:
        cursor = conn.cursor()
        set_clauses = []
        values = []
        for k, v in updates.items():
            if k == "profile_completed":
                set_clauses.append(f"{k} = ?")
                values.append(1 if v else 0)
            else:
                set_clauses.append(f"{k} = ?")
                values.append(v)
        values.append(user_id)

        sql = f"UPDATE users SET {', '.join(set_clauses)} WHERE id = ?"
        cursor.execute(sql, tuple(values))
        conn.commit()

    return get_user_by_id(user_id)


# ── Activity History DAL ──────────────────────────────────────────────────────

def create_activity(
    user_id: str,
    activity_type: str,
    title: str,
    query_text: Optional[str] = None,
    resource_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Persist an authenticated user activity record in Supabase and local SQLite."""
    activity_id = str(uuid.uuid4())
    now_iso = datetime.now(timezone.utc).isoformat()
    meta = metadata or {}

    payload = {
        "id": activity_id,
        "user_id": user_id,
        "activity_type": activity_type,
        "title": title.strip(),
        "query_text": query_text,
        "resource_id": resource_id,
        "metadata": meta,
        "created_at": now_iso,
    }

    client = get_supabase_client()
    if client:
        try:
            client.table("user_activity_history").insert(payload).execute()
        except Exception as e:
            log.warning(f"Supabase create_activity failed: {e}. Writing to local SQLite.", extra={"component": "USER_REPO"})

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO user_activity_history (
                id, user_id, activity_type, title, query_text, resource_id, metadata, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                activity_id,
                user_id,
                activity_type,
                title.strip(),
                query_text,
                resource_id,
                json.dumps(meta),
                now_iso,
            ),
        )
        conn.commit()

    return payload


def get_user_activities(
    user_id: str,
    activity_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    """Retrieve isolated activity history for a verified user ID with pagination."""
    client = get_supabase_client()
    if client:
        try:
            query = client.table("user_activity_history").select("*").eq("user_id", user_id)
            if activity_type:
                query = query.eq("activity_type", activity_type)
            res = query.order("created_at", desc=True).range(offset, offset + limit - 1).execute()
            if res.data:
                return [dict(r) for r in res.data]
        except Exception as e:
            log.warning(f"Supabase get_user_activities failed: {e}. Reading SQLite.", extra={"component": "USER_REPO"})

    with get_db_connection() as conn:
        cursor = conn.cursor()
        if activity_type:
            cursor.execute(
                """SELECT id, user_id, activity_type, title, query_text, resource_id, metadata, created_at
                   FROM user_activity_history
                   WHERE user_id = ? AND activity_type = ?
                   ORDER BY created_at DESC
                   LIMIT ? OFFSET ?""",
                (user_id, activity_type, limit, offset),
            )
        else:
            cursor.execute(
                """SELECT id, user_id, activity_type, title, query_text, resource_id, metadata, created_at
                   FROM user_activity_history
                   WHERE user_id = ?
                   ORDER BY created_at DESC
                   LIMIT ? OFFSET ?""",
                (user_id, limit, offset),
            )
        rows = cursor.fetchall()
        result = []
        for r in rows:
            d = dict(r)
            if isinstance(d.get("metadata"), str):
                try:
                    d["metadata"] = json.loads(d["metadata"])
                except Exception:
                    d["metadata"] = {}
            result.append(d)
        return result


def delete_activity_by_id(activity_id: str, user_id: str) -> bool:
    """Safely delete an activity record ensuring ownership check."""
    client = get_supabase_client()
    if client:
        try:
            res = client.table("user_activity_history").delete().eq("id", activity_id).eq("user_id", user_id).execute()
            if res.data:
                return True
        except Exception as e:
            log.warning(f"Supabase delete_activity failed: {e}", extra={"component": "USER_REPO"})

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM user_activity_history WHERE id = ? AND user_id = ?", (activity_id, user_id))
        conn.commit()
        return cursor.rowcount > 0
