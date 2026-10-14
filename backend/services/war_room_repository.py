"""
NyayaSarathi Legal War Room — Persistence Repository
Handles SQLite storage and retrieval for War Room sessions, editable analysis,
token usage logs, and caching.
"""

import os
import json
import sqlite3
import hashlib
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from logger import get_logger

log = get_logger("nyayasarathi.war_room_repo")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "nyayasarathi.db")


def get_db_connection() -> sqlite3.Connection:
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_war_room_tables():
    """Initializes SQLite tables for War Room sessions, usage logs, and cache."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS war_room_sessions (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                case_id TEXT,
                title TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                case_type TEXT NOT NULL DEFAULT 'general',
                jurisdiction TEXT NOT NULL DEFAULT 'High Court',
                court TEXT NOT NULL DEFAULT '',
                user_position TEXT NOT NULL DEFAULT 'petitioner',
                opposing_party TEXT NOT NULL DEFAULT '',
                relevant_dates_json TEXT NOT NULL DEFAULT '[]',
                selected_doc_ids_json TEXT NOT NULL DEFAULT '[]',
                case_overview_json TEXT NOT NULL DEFAULT '{}',
                fact_sheet_json TEXT NOT NULL DEFAULT '[]',
                evidence_findings_json TEXT NOT NULL DEFAULT '[]',
                arguments_json TEXT NOT NULL DEFAULT '[]',
                opposition_json TEXT NOT NULL DEFAULT '[]',
                risks_json TEXT NOT NULL DEFAULT '[]',
                precedents_json TEXT NOT NULL DEFAULT '[]',
                report_json TEXT NOT NULL DEFAULT '{}',
                version INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_war_room_user ON war_room_sessions(user_id);
            CREATE INDEX IF NOT EXISTS idx_war_room_updated ON war_room_sessions(updated_at);

            CREATE TABLE IF NOT EXISTS war_room_cache (
                cache_key TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                operation TEXT NOT NULL,
                result_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_war_room_cache_session ON war_room_cache(session_id);

            CREATE TABLE IF NOT EXISTS war_room_usage_log (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                user_id TEXT,
                operation TEXT NOT NULL,
                provider TEXT NOT NULL,
                model TEXT NOT NULL,
                input_tokens INTEGER NOT NULL DEFAULT 0,
                output_tokens INTEGER NOT NULL DEFAULT 0,
                duration_ms INTEGER NOT NULL DEFAULT 0,
                cache_hit INTEGER NOT NULL DEFAULT 0,
                error TEXT,
                created_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_war_room_usage_session ON war_room_usage_log(session_id);
        """)
        # Safe migrations for existing SQLite databases
        cursor.execute("PRAGMA table_info(war_room_sessions)")
        existing_cols = {col["name"] for col in cursor.fetchall()}
        if "case_id" not in existing_cols:
            cursor.execute("ALTER TABLE war_room_sessions ADD COLUMN case_id TEXT")
        if "case_overview_json" not in existing_cols:
            cursor.execute("ALTER TABLE war_room_sessions ADD COLUMN case_overview_json TEXT NOT NULL DEFAULT '{}'")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_war_room_case ON war_room_sessions(case_id)")
        conn.commit()
    log.info("War Room tables initialized successfully.", extra={"component": "WAR_ROOM_REPO"})


def create_session(session_data: Dict[str, Any]) -> Dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    session_id = session_data["id"]
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO war_room_sessions (
                id, user_id, case_id, title, description, case_type, jurisdiction, court,
                user_position, opposing_party, relevant_dates_json, selected_doc_ids_json,
                case_overview_json, fact_sheet_json, evidence_findings_json, arguments_json,
                opposition_json, risks_json, precedents_json, report_json, version, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session_id,
            session_data.get("user_id"),
            session_data.get("case_id"),
            session_data.get("title", "Untitled War Room"),
            session_data.get("description", ""),
            session_data.get("case_type", "general"),
            session_data.get("jurisdiction", "High Court"),
            session_data.get("court", ""),
            session_data.get("user_position", "petitioner"),
            session_data.get("opposing_party", ""),
            json.dumps(session_data.get("relevant_dates", [])),
            json.dumps(session_data.get("selected_doc_ids", [])),
            json.dumps(session_data.get("case_overview", {})),
            json.dumps(session_data.get("fact_sheet", [])),
            json.dumps(session_data.get("evidence_findings", [])),
            json.dumps(session_data.get("arguments", [])),
            json.dumps(session_data.get("opposition", [])),
            json.dumps(session_data.get("risks", [])),
            json.dumps(session_data.get("precedents", [])),
            json.dumps(session_data.get("report", {})),
            1,
            now,
            now,
        ))
        conn.commit()
    return get_session_by_id(session_id)  # type: ignore


def get_session_by_id(session_id: str) -> Optional[Dict[str, Any]]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM war_room_sessions WHERE id = ?", (session_id,))
        row = cursor.fetchone()
        if not row:
            return None
        return _row_to_dict(row)


def list_sessions(user_id: Optional[str] = None) -> List[Dict[str, Any]]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        if user_id:
            cursor.execute("""
                SELECT * FROM war_room_sessions
                WHERE user_id = ? OR user_id IS NULL
                ORDER BY updated_at DESC
            """, (user_id,))
        else:
            cursor.execute("SELECT * FROM war_room_sessions ORDER BY updated_at DESC")
        rows = cursor.fetchall()
        return [_row_to_dict(r) for r in rows]


def update_session(session_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    existing = get_session_by_id(session_id)
    if not existing:
        return None

    now = datetime.now(timezone.utc).isoformat()
    fields = []
    values = []

    for key, val in updates.items():
        if key in ("title", "description", "case_type", "jurisdiction", "court", "user_position", "opposing_party", "case_id"):
            fields.append(f"{key} = ?")
            values.append(val)
        elif key in ("relevant_dates", "selected_doc_ids", "case_overview", "fact_sheet", "evidence_findings", "arguments", "opposition", "risks", "precedents", "report"):
            fields.append(f"{key}_json = ?")
            values.append(json.dumps(val))

    if not fields:
        return existing

    fields.append("version = version + 1")
    fields.append("updated_at = ?")
    values.append(now)
    values.append(session_id)

    with get_db_connection() as conn:
        cursor = conn.cursor()
        query = f"UPDATE war_room_sessions SET {', '.join(fields)} WHERE id = ?"
        cursor.execute(query, tuple(values))
        conn.commit()

    return get_session_by_id(session_id)


def delete_session(session_id: str) -> bool:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM war_room_sessions WHERE id = ?", (session_id,))
        cursor.execute("DELETE FROM war_room_cache WHERE session_id = ?", (session_id,))
        cursor.execute("DELETE FROM war_room_usage_log WHERE session_id = ?", (session_id,))
        conn.commit()
        return cursor.rowcount > 0


def _row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    # Support backward-compatible access if case_id or case_overview_json not present in row
    keys = row.keys() if hasattr(row, "keys") else []
    return {
        "id": row["id"],
        "user_id": row["user_id"],
        "case_id": row["case_id"] if "case_id" in keys else None,
        "title": row["title"],
        "description": row["description"],
        "case_type": row["case_type"],
        "jurisdiction": row["jurisdiction"],
        "court": row["court"],
        "user_position": row["user_position"],
        "opposing_party": row["opposing_party"],
        "relevant_dates": json.loads(row["relevant_dates_json"] or "[]"),
        "selected_doc_ids": json.loads(row["selected_doc_ids_json"] or "[]"),
        "case_overview": json.loads(row["case_overview_json"] or "{}") if "case_overview_json" in keys else {},
        "fact_sheet": json.loads(row["fact_sheet_json"] or "[]"),
        "evidence_findings": json.loads(row["evidence_findings_json"] or "[]"),
        "arguments": json.loads(row["arguments_json"] or "[]"),
        "opposition": json.loads(row["opposition_json"] or "[]"),
        "risks": json.loads(row["risks_json"] or "[]"),
        "precedents": json.loads(row["precedents_json"] or "[]"),
        "report": json.loads(row["report_json"] or "{}"),
        "version": row["version"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


# ── Cache Methods ─────────────────────────────────────────────────────────────

def get_cache(cache_key: str) -> Optional[Dict[str, Any]]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT result_json FROM war_room_cache WHERE cache_key = ?", (cache_key,))
        row = cursor.fetchone()
        if row:
            try:
                return json.loads(row["result_json"])
            except Exception:
                return None
        return None


def set_cache(cache_key: str, session_id: str, operation: str, result: Any):
    now = datetime.now(timezone.utc).isoformat()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO war_room_cache (cache_key, session_id, operation, result_json, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (cache_key, session_id, operation, json.dumps(result), now))
        conn.commit()


def invalidate_session_cache(session_id: str):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM war_room_cache WHERE session_id = ?", (session_id,))
        conn.commit()


# ── Usage Log Methods ─────────────────────────────────────────────────────────

def log_usage(
    log_id: str,
    session_id: str,
    user_id: Optional[str],
    operation: str,
    provider: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
    duration_ms: int,
    cache_hit: bool = False,
    error: Optional[str] = None,
):
    now = datetime.now(timezone.utc).isoformat()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO war_room_usage_log (
                id, session_id, user_id, operation, provider, model,
                input_tokens, output_tokens, duration_ms, cache_hit, error, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            log_id,
            session_id,
            user_id,
            operation,
            provider,
            model,
            input_tokens,
            output_tokens,
            duration_ms,
            1 if cache_hit else 0,
            error,
            now,
        ))
        conn.commit()


def get_session_usage_summary(session_id: str) -> Dict[str, Any]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                COUNT(*) as total_requests,
                SUM(input_tokens) as total_input_tokens,
                SUM(output_tokens) as total_output_tokens,
                SUM(duration_ms) as total_duration_ms,
                SUM(cache_hit) as total_cache_hits
            FROM war_room_usage_log
            WHERE session_id = ?
        """, (session_id,))
        row = cursor.fetchone()
        return {
            "total_requests": row["total_requests"] or 0,
            "total_input_tokens": row["total_input_tokens"] or 0,
            "total_output_tokens": row["total_output_tokens"] or 0,
            "total_tokens": (row["total_input_tokens"] or 0) + (row["total_output_tokens"] or 0),
            "total_duration_ms": row["total_duration_ms"] or 0,
            "total_cache_hits": row["total_cache_hits"] or 0,
        }
