"""
NyayaSarathi User & History Repository
Decoupled Data Access Layer for User Profiles, Role Auditing, Activity History, and Case Assignments.
Supports authoritative PostgreSQL (Supabase) in production and standalone SQLite for local development and tests.
Enforces transactional integrity, durable audit retention, and robust role authorization.
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

try:
    import psycopg2
    import psycopg2.extras
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False


def is_postgres_authoritative() -> bool:
    """
    Determine if PostgreSQL is the authoritative production database.
    Can be explicitly disabled for offline unit tests via NYAYASARATHI_USE_SQLITE=1.
    """
    if os.getenv("NYAYASARATHI_USE_SQLITE", "0") == "1":
        return False
    if not PSYCOPG2_AVAILABLE:
        return False
    db_url = os.getenv("DATABASE_URL")
    return bool(db_url and db_url.strip() and "dummy" not in db_url.lower())


def get_pg_connection():
    """Get raw connection to authoritative PostgreSQL database with autocommit disabled."""
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL environment variable is missing.")
    return psycopg2.connect(db_url)


def get_db_connection() -> sqlite3.Connection:
    """Get connection to local SQLite database with Row factory."""
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_user_table():
    """
    Auto-initialize database tables in SQLite (for local/testing fallback mode).
    Schema matches PostgreSQL/Supabase conventions.
    """
    log.info("Initializing user database tables in SQLite...", extra={"component": "USER_REPO"})
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

        # Create role_change_audit in SQLite with SET NULL and snapshots
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS role_change_audit (
                id TEXT PRIMARY KEY,
                target_user_id TEXT,
                actor_user_id TEXT,
                old_role TEXT NOT NULL,
                new_role TEXT NOT NULL,
                reason TEXT,
                created_at TEXT NOT NULL,
                target_email TEXT,
                actor_email TEXT,
                actor_name TEXT,
                FOREIGN KEY (target_user_id) REFERENCES users(id) ON DELETE SET NULL,
                FOREIGN KEY (actor_user_id) REFERENCES users(id) ON DELETE SET NULL
            )
        """)
        cursor.execute("PRAGMA table_info(role_change_audit)")
        existing_audit_cols = {row["name"] for row in cursor.fetchall()}
        if "target_email" not in existing_audit_cols:
            cursor.execute("ALTER TABLE role_change_audit ADD COLUMN target_email TEXT")
        if "actor_email" not in existing_audit_cols:
            cursor.execute("ALTER TABLE role_change_audit ADD COLUMN actor_email TEXT")
        if "actor_name" not in existing_audit_cols:
            cursor.execute("ALTER TABLE role_change_audit ADD COLUMN actor_name TEXT")

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_role_audit_target ON role_change_audit(target_user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_role_audit_created ON role_change_audit(created_at DESC)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_role_audit_actor ON role_change_audit(actor_user_id)")

        # Create judge_case_assignments in SQLite
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS judge_case_assignments (
                id TEXT PRIMARY KEY,
                case_number TEXT NOT NULL,
                title TEXT NOT NULL,
                court_name TEXT NOT NULL,
                case_type TEXT NOT NULL DEFAULT 'Criminal',
                judge_id TEXT NOT NULL,
                assigned_by_id TEXT,
                status TEXT NOT NULL DEFAULT 'ASSIGNED',
                priority TEXT NOT NULL DEFAULT 'REGULAR',
                filing_date TEXT,
                hearing_date TEXT,
                petitioner TEXT,
                respondent TEXT,
                notes TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (judge_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (assigned_by_id) REFERENCES users(id) ON DELETE SET NULL
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_case_assign_judge ON judge_case_assignments(judge_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_case_assign_status ON judge_case_assignments(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_case_assign_case_num ON judge_case_assignments(case_number)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_case_assign_created ON judge_case_assignments(created_at DESC)")

        conn.commit()
    log.info("User database tables ready.", extra={"component": "USER_REPO"})


# ── User Lookup & Profile DAL ────────────────────────────────────────────────

def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Retrieve user dictionary by email (case-insensitive) from authoritative store."""
    clean_email = email.strip()

    if is_postgres_authoritative():
        conn = get_pg_connection()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    """SELECT id, email, password_hash, full_name, role, avatar_url, 
                              organization, designation, profile_completed, google_sub, 
                              created_at, updated_at 
                       FROM public.users WHERE LOWER(email) = LOWER(%s) LIMIT 1""",
                    (clean_email,)
                )
                row = cur.fetchone()
                if row:
                    d = dict(row)
                    d["profile_completed"] = bool(d.get("profile_completed"))
                    return d
        finally:
            conn.close()

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

    if is_postgres_authoritative():
        conn = get_pg_connection()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    """SELECT id, email, password_hash, full_name, role, avatar_url, 
                              organization, designation, profile_completed, google_sub, 
                              created_at, updated_at 
                       FROM public.users WHERE google_sub = %s LIMIT 1""",
                    (google_sub,)
                )
                row = cur.fetchone()
                if row:
                    d = dict(row)
                    d["profile_completed"] = bool(d.get("profile_completed"))
                    return d
        finally:
            conn.close()

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
    """Retrieve user dictionary by ID from authoritative store."""
    if is_postgres_authoritative():
        conn = get_pg_connection()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    """SELECT id, email, password_hash, full_name, role, avatar_url, 
                              organization, designation, profile_completed, google_sub, 
                              created_at, updated_at 
                       FROM public.users WHERE id = %s LIMIT 1""",
                    (user_id,)
                )
                row = cur.fetchone()
                if row:
                    d = dict(row)
                    d["profile_completed"] = bool(d.get("profile_completed"))
                    return d
        finally:
            conn.close()

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
    """Create a new user in the authoritative store and mirror to local SQLite."""
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

    if is_postgres_authoritative():
        conn = get_pg_connection()
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """INSERT INTO public.users (
                            id, email, password_hash, full_name, role, avatar_url,
                            organization, designation, profile_completed, google_sub,
                            created_at, updated_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                        (
                            user_id, clean_email, password_hash, clean_name, role, avatar_url,
                            organization, designation, profile_completed, google_sub,
                            now_iso, now_iso
                        )
                    )
            log.info(f"User {clean_email} created in PostgreSQL.", extra={"component": "USER_REPO"})
        except Exception as e:
            log.error(f"Authoritative Postgres create_user failed: {e}", extra={"component": "USER_REPO"})
            raise e
        finally:
            conn.close()

    # Mirror to local SQLite
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
        updates["avatar_url"] = avatar_url.strip() or None
    if organization is not None:
        updates["organization"] = organization.strip() or None
    if designation is not None:
        updates["designation"] = designation.strip() or None
    if google_sub is not None:
        updates["google_sub"] = google_sub.strip() or None
    if profile_completed is not None:
        updates["profile_completed"] = bool(profile_completed)

    if is_postgres_authoritative():
        conn = get_pg_connection()
        try:
            with conn:
                with conn.cursor() as cur:
                    set_clauses = [f"{k} = %s" for k in updates.keys()]
                    values = list(updates.values()) + [user_id]
                    cur.execute(f"UPDATE public.users SET {', '.join(set_clauses)} WHERE id = %s", tuple(values))
        except Exception as e:
            log.error(f"Authoritative Postgres update_user_profile failed: {e}", extra={"component": "USER_REPO"})
            raise e
        finally:
            conn.close()

    # Mirror to local SQLite
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


def delete_user_by_id(user_id: str) -> bool:
    """
    Delete a user account by ID.
    Under Migration 003, role_change_audit records survive with target_user_id=NULL
    and immutable snapshot identity columns intact.
    """
    deleted = False
    if is_postgres_authoritative():
        conn = get_pg_connection()
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM public.users WHERE id = %s", (user_id,))
                    deleted = cur.rowcount > 0
        except Exception as e:
            log.error(f"Authoritative Postgres delete_user_by_id failed: {e}", extra={"component": "USER_REPO"})
            raise e
        finally:
            conn.close()

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        if not is_postgres_authoritative():
            deleted = cursor.rowcount > 0

    return deleted


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

    if is_postgres_authoritative():
        conn = get_pg_connection()
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """INSERT INTO public.user_activity_history (
                            id, user_id, activity_type, title, query_text, resource_id, metadata, created_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                        (activity_id, user_id, activity_type, title.strip(), query_text, resource_id, json.dumps(meta), now_iso)
                    )
        except Exception as e:
            log.error(f"Authoritative Postgres create_activity failed: {e}", extra={"component": "USER_REPO"})
            raise e
        finally:
            conn.close()

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


def count_user_activities(user_id: str, activity_type: Optional[str] = None) -> int:
    """Return total count of activity records for a user, optionally filtered by type."""
    if is_postgres_authoritative():
        conn = get_pg_connection()
        try:
            with conn.cursor() as cur:
                if activity_type:
                    cur.execute(
                        "SELECT COUNT(*) FROM public.user_activity_history WHERE user_id = %s AND activity_type = %s",
                        (user_id, activity_type),
                    )
                else:
                    cur.execute(
                        "SELECT COUNT(*) FROM public.user_activity_history WHERE user_id = %s",
                        (user_id,),
                    )
                row = cur.fetchone()
                return int(row[0]) if row else 0
        finally:
            conn.close()

    with get_db_connection() as conn:
        cursor = conn.cursor()
        if activity_type:
            cursor.execute(
                "SELECT COUNT(*) FROM user_activity_history WHERE user_id = ? AND activity_type = ?",
                (user_id, activity_type),
            )
        else:
            cursor.execute(
                "SELECT COUNT(*) FROM user_activity_history WHERE user_id = ?",
                (user_id,),
            )
        row = cursor.fetchone()
        return int(row[0]) if row else 0


def get_user_activities(
    user_id: str,
    activity_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    """Retrieve isolated activity history for a verified user ID with pagination."""
    if is_postgres_authoritative():
        conn = get_pg_connection()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                query = "SELECT id, user_id, activity_type, title, query_text, resource_id, metadata, created_at FROM public.user_activity_history WHERE user_id = %s"
                params = [user_id]
                if activity_type:
                    query += " AND activity_type = %s"
                    params.append(activity_type)
                query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
                params.extend([limit, offset])

                cur.execute(query, tuple(params))
                rows = cur.fetchall()
                result = []
                for r in rows:
                    d = dict(r)
                    if hasattr(d.get("created_at"), "isoformat"):
                        d["created_at"] = d["created_at"].isoformat()
                    if isinstance(d.get("metadata"), str):
                        try:
                            d["metadata"] = json.loads(d["metadata"])
                        except Exception:
                            d["metadata"] = {}
                    result.append(d)
                return result
        finally:
            conn.close()

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
    deleted = False
    if is_postgres_authoritative():
        conn = get_pg_connection()
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "DELETE FROM public.user_activity_history WHERE id = %s AND user_id = %s",
                        (activity_id, user_id)
                    )
                    deleted = cur.rowcount > 0
        finally:
            conn.close()

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM user_activity_history WHERE id = ? AND user_id = ?", (activity_id, user_id))
        conn.commit()
        if not is_postgres_authoritative():
            deleted = cursor.rowcount > 0

    return deleted


# ── Role Management & Audit DAL ──────────────────────────────────────────────

def count_active_admins() -> int:
    """Return count of users with the ADMIN role from authoritative store."""
    if is_postgres_authoritative():
        conn = get_pg_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM public.users WHERE role = 'ADMIN'")
                return cur.fetchone()[0]
        finally:
            conn.close()

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'ADMIN'")
        return cursor.fetchone()[0]


def update_user_role_with_audit(
    target_user_id: str,
    actor_user_id: str,
    new_role: str,
    reason: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Safely update a target user's role and persist an immutable audit record with identity snapshots.
    Executes in a single atomic transaction on the authoritative database.
    If the authoritative write fails, raises an exception and NEVER silently falls back.
    """
    target_user = get_user_by_id(target_user_id)
    if not target_user:
        raise ValueError(f"Target user with id '{target_user_id}' does not exist.")

    actor_user = get_user_by_id(actor_user_id) if actor_user_id else None

    old_role = target_user.get("role", "USER")
    audit_id = str(uuid.uuid4())
    now_iso = datetime.now(timezone.utc).isoformat()
    clean_reason = reason.strip() if reason and reason.strip() else None

    # Capture immutable snapshots of identity at the time of role change
    target_email = target_user.get("email")
    actor_email = actor_user.get("email") if actor_user else None
    actor_name = actor_user.get("full_name") if actor_user else None

    audit_payload = {
        "id": audit_id,
        "audit_id": audit_id,
        "target_user_id": target_user_id,
        "actor_user_id": actor_user_id,
        "old_role": old_role,
        "new_role": new_role,
        "reason": clean_reason,
        "created_at": now_iso,
        "target_email": target_email,
        "actor_email": actor_email,
        "actor_name": actor_name,
    }

    if is_postgres_authoritative():
        # Authoritative PostgreSQL Atomic Transaction
        conn = get_pg_connection()
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE public.users SET role = %s, updated_at = %s WHERE id = %s",
                        (new_role, now_iso, target_user_id)
                    )
                    if cur.rowcount == 0:
                        raise ValueError(f"Target user with id '{target_user_id}' not found in authoritative database")
                    cur.execute(
                        """INSERT INTO public.role_change_audit (
                            id, target_user_id, actor_user_id, old_role, new_role, reason,
                            created_at, target_email, actor_email, actor_name
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                        (
                            audit_id, target_user_id, actor_user_id, old_role, new_role, clean_reason,
                            now_iso, target_email, actor_email, actor_name
                        )
                    )
            log.info(f"Role updated transactionally in PostgreSQL: {target_user_id} -> {new_role}", extra={"component": "USER_REPO"})
        except Exception as exc:
            log.error(f"Authoritative PostgreSQL role update transaction failed: {exc}", extra={"component": "USER_REPO"})
            raise exc
        finally:
            conn.close()

        # Best-effort mirror to SQLite replica
        try:
            with get_db_connection() as sconn:
                scur = sconn.cursor()
                scur.execute("UPDATE users SET role = ?, updated_at = ? WHERE id = ?", (new_role, now_iso, target_user_id))
                scur.execute(
                    """INSERT OR REPLACE INTO role_change_audit (
                        id, target_user_id, actor_user_id, old_role, new_role, reason,
                        created_at, target_email, actor_email, actor_name
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (audit_id, target_user_id, actor_user_id, old_role, new_role, clean_reason,
                     now_iso, target_email, actor_email, actor_name)
                )
                sconn.commit()
        except Exception as e:
            log.debug(f"Non-fatal SQLite mirror failed: {e}")

    else:
        # SQLite transaction
        with get_db_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("UPDATE users SET role = ?, updated_at = ? WHERE id = ?", (new_role, now_iso, target_user_id))
                cursor.execute(
                    """INSERT INTO role_change_audit (
                        id, target_user_id, actor_user_id, old_role, new_role, reason,
                        created_at, target_email, actor_email, actor_name
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (audit_id, target_user_id, actor_user_id, old_role, new_role, clean_reason,
                     now_iso, target_email, actor_email, actor_name),
                )
                conn.commit()
            except Exception as exc:
                conn.rollback()
                log.error(f"Failed to update role in SQLite: {exc}", extra={"component": "USER_REPO"})
                raise exc

    return audit_payload


def get_role_audit_history(
    limit: int = 50,
    offset: int = 0,
    target_user_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Retrieve role-change audit records joined with target and actor profiles.
    Uses COALESCE against immutable snapshots so historical audits remain fully readable
    even if the corresponding account was subsequently deleted.
    """
    if is_postgres_authoritative():
        conn = get_pg_connection()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                query = """
                    SELECT 
                        a.id, a.target_user_id, a.actor_user_id, a.old_role, a.new_role, a.reason, a.created_at,
                        COALESCE(u_target.full_name, a.target_email, 'Deleted Account') AS target_name,
                        COALESCE(u_target.email, a.target_email, 'unknown@deleted') AS target_email,
                        COALESCE(u_actor.full_name, a.actor_name, 'System Administrator') AS actor_name,
                        COALESCE(u_actor.email, a.actor_email, 'admin@deleted') AS actor_email
                    FROM public.role_change_audit a
                    LEFT JOIN public.users u_target ON a.target_user_id = u_target.id
                    LEFT JOIN public.users u_actor ON a.actor_user_id = u_actor.id
                """
                params = []
                if target_user_id:
                    query += " WHERE a.target_user_id = %s"
                    params.append(target_user_id)
                query += " ORDER BY a.created_at DESC LIMIT %s OFFSET %s"
                params.extend([limit, offset])

                cur.execute(query, tuple(params))
                rows = cur.fetchall()
                results = []
                for r in rows:
                    d = dict(r)
                    if hasattr(d.get("created_at"), "isoformat"):
                        d["created_at"] = d["created_at"].isoformat()
                    results.append(d)
                return results
        finally:
            conn.close()

    with get_db_connection() as conn:
        cursor = conn.cursor()
        query = """
            SELECT 
                a.id, a.target_user_id, a.actor_user_id, a.old_role, a.new_role, a.reason, a.created_at,
                COALESCE(u_target.full_name, a.target_email, 'Deleted Account') AS target_name,
                COALESCE(u_target.email, a.target_email, 'unknown@deleted') AS target_email,
                COALESCE(u_actor.full_name, a.actor_name, 'System Administrator') AS actor_name,
                COALESCE(u_actor.email, a.actor_email, 'admin@deleted') AS actor_email
            FROM role_change_audit a
            LEFT JOIN users u_target ON a.target_user_id = u_target.id
            LEFT JOIN users u_actor ON a.actor_user_id = u_actor.id
        """
        params = []
        if target_user_id:
            query += " WHERE a.target_user_id = ?"
            params.append(target_user_id)
        query += " ORDER BY a.created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor.execute(query, tuple(params))
        return [dict(r) for r in cursor.fetchall()]


def count_role_audits(target_user_id: Optional[str] = None) -> int:
    """Return total count of role audit entries from authoritative store."""
    if is_postgres_authoritative():
        conn = get_pg_connection()
        try:
            with conn.cursor() as cur:
                if target_user_id:
                    cur.execute("SELECT COUNT(*) FROM public.role_change_audit WHERE target_user_id = %s", (target_user_id,))
                else:
                    cur.execute("SELECT COUNT(*) FROM public.role_change_audit")
                return cur.fetchone()[0]
        finally:
            conn.close()

    with get_db_connection() as conn:
        cursor = conn.cursor()
        if target_user_id:
            cursor.execute("SELECT COUNT(*) FROM role_change_audit WHERE target_user_id = ?", (target_user_id,))
        else:
            cursor.execute("SELECT COUNT(*) FROM role_change_audit")
        return cursor.fetchone()[0]


def list_users(
    search: Optional[str] = None,
    role: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """Retrieve paginated user list with optional keyword search and role filter from authoritative store."""
    if is_postgres_authoritative():
        conn = get_pg_connection()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                clauses = []
                params = []
                if search and search.strip():
                    term = f"%{search.strip()}%"
                    clauses.append("(full_name ILIKE %s OR email ILIKE %s)")
                    params.extend([term, term])
                if role and role.strip() and role.strip().upper() != "ALL":
                    clauses.append("role = %s")
                    params.append(role.strip().upper())

                where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
                query = f"""
                    SELECT id, email, full_name, role, avatar_url, organization, designation, profile_completed, created_at, updated_at
                    FROM public.users
                    {where_sql}
                    ORDER BY created_at DESC
                    LIMIT %s OFFSET %s
                """
                params.extend([limit, offset])
                cur.execute(query, tuple(params))
                rows = cur.fetchall()
                result = []
                for r in rows:
                    d = dict(r)
                    d["profile_completed"] = bool(d.get("profile_completed"))
                    if hasattr(d.get("created_at"), "isoformat"):
                        d["created_at"] = d["created_at"].isoformat()
                    if hasattr(d.get("updated_at"), "isoformat"):
                        d["updated_at"] = d["updated_at"].isoformat()
                    result.append(d)
                return result
        finally:
            conn.close()

    with get_db_connection() as conn:
        cursor = conn.cursor()
        clauses = []
        params = []
        if search and search.strip():
            term = f"%{search.strip()}%"
            clauses.append("(LOWER(full_name) LIKE LOWER(?) OR LOWER(email) LIKE LOWER(?))")
            params.extend([term, term])
        if role and role.strip() and role.strip().upper() != "ALL":
            clauses.append("role = ?")
            params.append(role.strip().upper())

        where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        query = f"""
            SELECT id, email, full_name, role, avatar_url, organization, designation, profile_completed, created_at, updated_at
            FROM users
            {where_sql}
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """
        params.extend([limit, offset])
        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["profile_completed"] = bool(d.get("profile_completed"))
            result.append(d)
        return result


def count_users(search: Optional[str] = None, role: Optional[str] = None) -> int:
    """Return total count of users matching search and role filters from authoritative store."""
    if is_postgres_authoritative():
        conn = get_pg_connection()
        try:
            with conn.cursor() as cur:
                clauses = []
                params = []
                if search and search.strip():
                    term = f"%{search.strip()}%"
                    clauses.append("(full_name ILIKE %s OR email ILIKE %s)")
                    params.extend([term, term])
                if role and role.strip() and role.strip().upper() != "ALL":
                    clauses.append("role = %s")
                    params.append(role.strip().upper())

                where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
                cur.execute(f"SELECT COUNT(*) FROM public.users {where_sql}", tuple(params))
                return cur.fetchone()[0]
        finally:
            conn.close()

    with get_db_connection() as conn:
        cursor = conn.cursor()
        clauses = []
        params = []
        if search and search.strip():
            term = f"%{search.strip()}%"
            clauses.append("(LOWER(full_name) LIKE LOWER(?) OR LOWER(email) LIKE LOWER(?))")
            params.extend([term, term])
        if role and role.strip() and role.strip().upper() != "ALL":
            clauses.append("role = ?")
            params.append(role.strip().upper())

        where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        cursor.execute(f"SELECT COUNT(*) FROM users {where_sql}", tuple(params))
        return cursor.fetchone()[0]


def get_admin_metrics() -> Dict[str, Any]:
    """Compile real system-level statistics from the authoritative database."""
    if is_postgres_authoritative():
        conn = get_pg_connection()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT COUNT(*) FROM public.users")
                total_users = cur.fetchone()["count"]

                cur.execute("SELECT role, COUNT(*) AS count FROM public.users GROUP BY role")
                role_counts = {r["role"]: r["count"] for r in cur.fetchall()}

                cur.execute("""
                    SELECT id, email, full_name, role, avatar_url, organization, designation, created_at
                    FROM public.users ORDER BY created_at DESC LIMIT 5
                """)
                recent_users = []
                for r in cur.fetchall():
                    d = dict(r)
                    if hasattr(d.get("created_at"), "isoformat"):
                        d["created_at"] = d["created_at"].isoformat()
                    recent_users.append(d)

                cur.execute("SELECT COUNT(*) FROM public.user_activity_history")
                total_activities = cur.fetchone()["count"]

                try:
                    cur.execute("SELECT COUNT(*) FROM public.judgments")
                    total_judgments = cur.fetchone()["count"]
                except Exception:
                    total_judgments = 0

            recent_audits = get_role_audit_history(limit=5, offset=0)

            return {
                "total_users": total_users,
                "role_counts": role_counts,
                "recent_users": recent_users,
                "recent_role_changes": recent_audits,
                "total_activities": total_activities,
                "total_judgments": total_judgments,
            }
        finally:
            conn.close()

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]

        cursor.execute("SELECT role, COUNT(*) FROM users GROUP BY role")
        role_counts = {r[0]: r[1] for r in cursor.fetchall()}

        cursor.execute("""
            SELECT id, email, full_name, role, avatar_url, organization, designation, created_at
            FROM users ORDER BY created_at DESC LIMIT 5
        """)
        recent_users = [dict(r) for r in cursor.fetchall()]

        recent_audits = get_role_audit_history(limit=5, offset=0)

        cursor.execute("SELECT COUNT(*) FROM user_activity_history")
        total_activities = cursor.fetchone()[0]

        try:
            cursor.execute("SELECT COUNT(*) FROM judgments")
            total_judgments = cursor.fetchone()[0]
        except Exception:
            total_judgments = 0

        return {
            "total_users": total_users,
            "role_counts": role_counts,
            "recent_users": recent_users,
            "recent_role_changes": recent_audits,
            "total_activities": total_activities,
            "total_judgments": total_judgments,
        }


# ── Case Assignment DAL ───────────────────────────────────────────────────────

def create_case_assignment(
    case_number: str,
    title: str,
    court_name: str,
    judge_id: str,
    assigned_by_id: Optional[str] = None,
    case_type: str = "Criminal",
    priority: str = "REGULAR",
    filing_date: Optional[str] = None,
    hearing_date: Optional[str] = None,
    petitioner: Optional[str] = None,
    respondent: Optional[str] = None,
    notes: Optional[str] = None,
) -> Dict[str, Any]:
    """Persist a persistent matter assignment to a designated judge in the authoritative database."""
    assignment_id = str(uuid.uuid4())
    now_iso = datetime.now(timezone.utc).isoformat()

    payload = {
        "id": assignment_id,
        "case_number": case_number.strip(),
        "title": title.strip(),
        "court_name": court_name.strip(),
        "case_type": case_type.strip(),
        "judge_id": judge_id,
        "assigned_by_id": assigned_by_id,
        "status": "ASSIGNED",
        "priority": priority.strip().upper(),
        "filing_date": filing_date,
        "hearing_date": hearing_date,
        "petitioner": petitioner.strip() if petitioner else None,
        "respondent": respondent.strip() if respondent else None,
        "notes": notes.strip() if notes else None,
        "created_at": now_iso,
        "updated_at": now_iso,
    }

    if is_postgres_authoritative():
        conn = get_pg_connection()
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """INSERT INTO public.judge_case_assignments (
                            id, case_number, title, court_name, case_type, judge_id, assigned_by_id,
                            status, priority, filing_date, hearing_date, petitioner, respondent, notes,
                            created_at, updated_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                        (
                            assignment_id, payload["case_number"], payload["title"], payload["court_name"],
                            payload["case_type"], judge_id, assigned_by_id, payload["status"], payload["priority"],
                            filing_date, hearing_date, payload["petitioner"], payload["respondent"], payload["notes"],
                            now_iso, now_iso
                        )
                    )
        except Exception as e:
            log.error(f"Authoritative Postgres create_case_assignment failed: {e}", extra={"component": "USER_REPO"})
            raise e
        finally:
            conn.close()

    # Mirror to local SQLite
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO judge_case_assignments (
                id, case_number, title, court_name, case_type, judge_id, assigned_by_id,
                status, priority, filing_date, hearing_date, petitioner, respondent, notes,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                assignment_id, payload["case_number"], payload["title"], payload["court_name"],
                payload["case_type"], judge_id, assigned_by_id, payload["status"], payload["priority"],
                filing_date, hearing_date, payload["petitioner"], payload["respondent"], payload["notes"],
                now_iso, now_iso
            ),
        )
        conn.commit()

    return payload


def get_judge_case_assignments(
    judge_id: str,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    """Retrieve case matters assigned to a specific judge with pagination and status filters."""
    if is_postgres_authoritative():
        conn = get_pg_connection()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                query = "SELECT * FROM public.judge_case_assignments WHERE judge_id = %s"
                params = [judge_id]
                if status:
                    query += " AND status = %s"
                    params.append(status.strip().upper())
                if priority:
                    query += " AND priority = %s"
                    params.append(priority.strip().upper())
                query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
                params.extend([limit, offset])

                cur.execute(query, tuple(params))
                rows = cur.fetchall()
                results = []
                for r in rows:
                    d = dict(r)
                    for date_field in ["filing_date", "hearing_date", "created_at", "updated_at"]:
                        if hasattr(d.get(date_field), "isoformat"):
                            d[date_field] = d[date_field].isoformat()
                    results.append(d)
                return results
        finally:
            conn.close()

    with get_db_connection() as conn:
        cursor = conn.cursor()
        query = "SELECT * FROM judge_case_assignments WHERE judge_id = ?"
        params = [judge_id]
        if status:
            query += " AND status = ?"
            params.append(status.strip().upper())
        if priority:
            query += " AND priority = ?"
            params.append(priority.strip().upper())
        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor.execute(query, tuple(params))
        return [dict(r) for r in cursor.fetchall()]


def count_judge_case_assignments(judge_id: str, status: Optional[str] = None) -> int:
    """Return count of assigned matters for a specific judge."""
    if is_postgres_authoritative():
        conn = get_pg_connection()
        try:
            with conn.cursor() as cur:
                query = "SELECT COUNT(*) FROM public.judge_case_assignments WHERE judge_id = %s"
                params = [judge_id]
                if status:
                    query += " AND status = %s"
                    params.append(status.strip().upper())
                cur.execute(query, tuple(params))
                return cur.fetchone()[0]
        finally:
            conn.close()

    with get_db_connection() as conn:
        cursor = conn.cursor()
        query = "SELECT COUNT(*) FROM judge_case_assignments WHERE judge_id = ?"
        params = [judge_id]
        if status:
            query += " AND status = ?"
            params.append(status.strip().upper())
        cursor.execute(query, tuple(params))
        return cursor.fetchone()[0]


def get_case_assignment_by_id(assignment_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve single case assignment by ID."""
    if is_postgres_authoritative():
        conn = get_pg_connection()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT * FROM public.judge_case_assignments WHERE id = %s", (assignment_id,))
                row = cur.fetchone()
                if row:
                    d = dict(row)
                    for date_field in ["filing_date", "hearing_date", "created_at", "updated_at"]:
                        if hasattr(d.get(date_field), "isoformat"):
                            d[date_field] = d[date_field].isoformat()
                    return d
        finally:
            conn.close()

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM judge_case_assignments WHERE id = ?", (assignment_id,))
        row = cursor.fetchone()
        if row:
            return dict(row)
    return None


def update_case_assignment_status(
    assignment_id: str,
    status: str,
    notes: Optional[str] = None,
    hearing_date: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Update progress status, hearing schedule, or judicial notes on an assigned matter."""
    now_iso = datetime.now(timezone.utc).isoformat()
    if is_postgres_authoritative():
        conn = get_pg_connection()
        try:
            with conn:
                with conn.cursor() as cur:
                    updates = ["status = %s", "updated_at = %s"]
                    params = [status.strip().upper(), now_iso]
                    if notes is not None:
                        updates.append("notes = %s")
                        params.append(notes.strip())
                    if hearing_date is not None:
                        updates.append("hearing_date = %s")
                        params.append(hearing_date.strip())
                    params.append(assignment_id)
                    cur.execute(f"UPDATE public.judge_case_assignments SET {', '.join(updates)} WHERE id = %s", tuple(params))
        finally:
            conn.close()

    with get_db_connection() as conn:
        cursor = conn.cursor()
        updates = ["status = ?", "updated_at = ?"]
        params = [status.strip().upper(), now_iso]
        if notes is not None:
            updates.append("notes = ?")
            params.append(notes.strip())
        if hearing_date is not None:
            updates.append("hearing_date = ?")
            params.append(hearing_date.strip())
        params.append(assignment_id)
        cursor.execute(f"UPDATE judge_case_assignments SET {', '.join(updates)} WHERE id = ?", tuple(params))
        conn.commit()

    return get_case_assignment_by_id(assignment_id)


def delete_case_assignment(assignment_id: str) -> bool:
    """Revoke or delete a case assignment."""
    deleted = False
    if is_postgres_authoritative():
        conn = get_pg_connection()
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM public.judge_case_assignments WHERE id = %s", (assignment_id,))
                    deleted = cur.rowcount > 0
        finally:
            conn.close()

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM judge_case_assignments WHERE id = ?", (assignment_id,))
        conn.commit()
        if not is_postgres_authoritative():
            deleted = cursor.rowcount > 0

    return deleted
