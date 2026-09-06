"""
NyayaSarathi User Repository
Decoupled Data Access Layer for User Accounts.
Currently connects to local SQLite (nyayasarathi.db) with auto-creation.
Easily swappable to Supabase (PostgreSQL / Supabase Python SDK) in the future.
"""

import os
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from logger import get_logger

log = get_logger("nyayasarathi.user_repo")

# Path to database
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
    Auto-initialize the `users` table in SQLite if it does not already exist.
    Schema matches PostgreSQL/Supabase conventions for seamless future migration.
    """
    log.info("Initializing user database table...", extra={"component": "USER_REPO"})
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'ADVOCATE',
                created_at TEXT NOT NULL
            )
        """)
        # Index on email for fast lookups
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
        conn.commit()
    log.info("User database table ready.", extra={"component": "USER_REPO"})


def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Retrieve user dictionary by email (case-insensitive)."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, email, password_hash, full_name, role, created_at FROM users WHERE LOWER(email) = LOWER(?)",
            (email.strip(),)
        )
        row = cursor.fetchone()
        if row:
            return dict(row)
    return None


def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve user dictionary by ID."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, email, password_hash, full_name, role, created_at FROM users WHERE id = ?",
            (user_id,)
        )
        row = cursor.fetchone()
        if row:
            return dict(row)
    return None


def create_user(email: str, password_hash: str, full_name: str, role: str = "ADVOCATE") -> Dict[str, Any]:
    """Create a new user and return the user record (excluding sensitive fields if needed)."""
    user_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc).isoformat()
    clean_email = email.strip().lower()
    clean_name = full_name.strip()

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO users (id, email, password_hash, full_name, role, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, clean_email, password_hash, clean_name, role, created_at)
        )
        conn.commit()

    return {
        "id": user_id,
        "email": clean_email,
        "full_name": clean_name,
        "role": role,
        "created_at": created_at,
    }
