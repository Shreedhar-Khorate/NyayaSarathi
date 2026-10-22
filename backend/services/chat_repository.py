"""
NyayaSarathi Chat Repository
Dual-mode persistence layer (PostgreSQL authoritative + SQLite fallback)
for real-time User–Advocate chat: conversations, messages, attachments,
and read-state cursors.

Security note: All participant checks are enforced here in the repository
and in the router. Caller must supply verified user IDs from JWT, never
from request body fields.
"""

import os
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from logger import get_logger
from services.user_repository import (
    is_postgres_authoritative,
    get_db_connection as _get_sqlite_conn,
    get_pg_connection,
)

log = get_logger("nyayasarathi.chat_repo")

# ── Maximum constraints ────────────────────────────────────────────────────────
MAX_MESSAGE_BODY_LEN = 4000        # characters
MAX_ATTACHMENT_BYTES = 10 * 1024 * 1024   # 10 MB
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
    "text/plain",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".gif", ".webp", ".txt", ".doc", ".docx"}


# ── SQLite helpers ─────────────────────────────────────────────────────────────

def _sqlite_conn() -> sqlite3.Connection:
    conn = _get_sqlite_conn()
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_chat_tables() -> None:
    """
    Auto-create chat tables in SQLite (local dev / fallback mode).
    Schema mirrors the PostgreSQL migration 006_chat_tables.sql.
    Called from main.py on_startup.
    """
    log.info("Initializing chat tables in SQLite...", extra={"component": "CHAT_REPO"})
    with _sqlite_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS chat_conversations (
                id              TEXT PRIMARY KEY,
                user_id         TEXT NOT NULL REFERENCES users(id),
                advocate_id     TEXT NOT NULL REFERENCES users(id),
                status          TEXT NOT NULL DEFAULT 'active',
                created_at      TEXT NOT NULL,
                updated_at      TEXT NOT NULL,
                last_message_at TEXT,
                UNIQUE (user_id, advocate_id)
            );

            CREATE INDEX IF NOT EXISTS idx_chat_conv_user
                ON chat_conversations(user_id);
            CREATE INDEX IF NOT EXISTS idx_chat_conv_advocate
                ON chat_conversations(advocate_id);
            CREATE INDEX IF NOT EXISTS idx_chat_conv_last_msg
                ON chat_conversations(last_message_at DESC);

            CREATE TABLE IF NOT EXISTS chat_messages (
                id              TEXT PRIMARY KEY,
                conversation_id TEXT NOT NULL REFERENCES chat_conversations(id),
                sender_id       TEXT NOT NULL REFERENCES users(id),
                body            TEXT,
                idempotency_key TEXT,
                created_at      TEXT NOT NULL,
                UNIQUE (conversation_id, idempotency_key)
            );

            CREATE INDEX IF NOT EXISTS idx_chat_msg_conv_created
                ON chat_messages(conversation_id, created_at, id);

            CREATE TABLE IF NOT EXISTS chat_attachments (
                id                TEXT PRIMARY KEY,
                message_id        TEXT NOT NULL REFERENCES chat_messages(id),
                conversation_id   TEXT NOT NULL REFERENCES chat_conversations(id),
                uploaded_by       TEXT NOT NULL REFERENCES users(id),
                storage_key       TEXT NOT NULL,
                original_filename TEXT NOT NULL,
                content_type      TEXT,
                size_bytes        INTEGER NOT NULL DEFAULT 0,
                created_at        TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_chat_attach_msg
                ON chat_attachments(message_id);

            CREATE TABLE IF NOT EXISTS chat_participant_state (
                conversation_id     TEXT NOT NULL REFERENCES chat_conversations(id),
                user_id             TEXT NOT NULL REFERENCES users(id),
                last_read_message_id TEXT,
                last_read_at        TEXT,
                updated_at          TEXT NOT NULL,
                PRIMARY KEY (conversation_id, user_id)
            );
        """)
    log.info("Chat SQLite tables ready.", extra={"component": "CHAT_REPO"})


# ── Timestamp helper ───────────────────────────────────────────────────────────

def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── Conversation operations ────────────────────────────────────────────────────

def get_or_create_conversation(
    user_id: str,
    advocate_id: str,
    current_user_id: str,
    current_user_role: str,
) -> Dict[str, Any]:
    """
    Idempotently create or retrieve a conversation between the given user and advocate.
    Only a USER can initiate (using their own user_id) or an ADVOCATE can initiate
    (using their own advocate_id). ADMIN may open any pair.
    Raises ValueError on invalid role pairings.
    """
    role = current_user_role.upper()
    if role == "USER" and current_user_id != user_id:
        raise PermissionError("USER can only create conversations for themselves.")
    if role == "ADVOCATE" and current_user_id != advocate_id:
        raise PermissionError("ADVOCATE can only participate in their own conversations.")
    if user_id == advocate_id:
        raise ValueError("user_id and advocate_id must differ.")

    from services.user_repository import get_user_by_id
    advocate_user = get_user_by_id(advocate_id)
    if advocate_user and advocate_user.get("role") != "ADVOCATE":
        raise ValueError("Selected advocate participant must have role ADVOCATE.")

    now = _utcnow()

    if is_postgres_authoritative():
        return _pg_get_or_create_conversation(user_id, advocate_id, now)
    return _sqlite_get_or_create_conversation(user_id, advocate_id, now)


def _pg_get_or_create_conversation(user_id: str, advocate_id: str, now: str) -> Dict[str, Any]:
    conn = get_pg_connection()
    try:
        with conn:
            with conn.cursor(cursor_factory=__import__("psycopg2.extras", fromlist=["RealDictCursor"]).RealDictCursor) as cur:
                cur.execute(
                    "SELECT * FROM public.chat_conversations WHERE user_id=%s AND advocate_id=%s",
                    (user_id, advocate_id),
                )
                row = cur.fetchone()
                if row:
                    return dict(row)
                conv_id = str(uuid.uuid4())
                cur.execute(
                    """INSERT INTO public.chat_conversations
                       (id, user_id, advocate_id, status, created_at, updated_at)
                       VALUES (%s, %s, %s, 'active', %s, %s)
                       ON CONFLICT (user_id, advocate_id) DO UPDATE SET updated_at = EXCLUDED.updated_at
                       RETURNING *""",
                    (conv_id, user_id, advocate_id, now, now),
                )
                return dict(cur.fetchone())
    finally:
        conn.close()


def _sqlite_get_or_create_conversation(user_id: str, advocate_id: str, now: str) -> Dict[str, Any]:
    with _sqlite_conn() as conn:
        row = conn.execute(
            "SELECT * FROM chat_conversations WHERE user_id=? AND advocate_id=?",
            (user_id, advocate_id),
        ).fetchone()
        if row:
            return dict(row)
        conv_id = str(uuid.uuid4())
        conn.execute(
            """INSERT OR IGNORE INTO chat_conversations
               (id, user_id, advocate_id, status, created_at, updated_at)
               VALUES (?,?,?,'active',?,?)""",
            (conv_id, user_id, advocate_id, now, now),
        )
        row = conn.execute(
            "SELECT * FROM chat_conversations WHERE user_id=? AND advocate_id=?",
            (user_id, advocate_id),
        ).fetchone()
        return dict(row)


def list_conversations(current_user_id: str, current_user_role: str) -> List[Dict[str, Any]]:
    """
    Return all conversations for the current user with unread count and last-message preview.
    USERs see conversations where they are user_id.
    ADVOCATEs see conversations where they are advocate_id.
    ADMINs see all (no private message content exposed).
    """
    if is_postgres_authoritative():
        return _pg_list_conversations(current_user_id, current_user_role)
    return _sqlite_list_conversations(current_user_id, current_user_role)


def _pg_list_conversations(uid: str, role: str) -> List[Dict[str, Any]]:
    import psycopg2.extras
    conn = get_pg_connection()
    try:
        with conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                where_clause, params = _participant_where_pg(uid, role)
                cur.execute(f"""
                    SELECT
                        c.*,
                        u.full_name AS other_party_name,
                        u.avatar_url AS other_party_avatar,
                        u.designation AS other_party_designation,
                        m.body AS last_message_body,
                        m.sender_id AS last_message_sender_id,
                        (
                            SELECT COUNT(*) FROM public.chat_messages cm
                            WHERE cm.conversation_id = c.id
                              AND cm.sender_id != %s
                              AND cm.created_at > COALESCE(
                                  (SELECT last_read_at FROM public.chat_participant_state
                                   WHERE conversation_id = c.id AND user_id = %s),
                                  '1970-01-01T00:00:00Z'
                              )
                        ) AS unread_count
                    FROM public.chat_conversations c
                    LEFT JOIN public.users u ON u.id = (
                        CASE WHEN c.user_id = %s THEN c.advocate_id ELSE c.user_id END
                    )
                    LEFT JOIN public.chat_messages m ON m.id = (
                        SELECT id FROM public.chat_messages
                        WHERE conversation_id = c.id
                        ORDER BY created_at DESC, id DESC
                        LIMIT 1
                    )
                    WHERE {where_clause}
                    ORDER BY COALESCE(c.last_message_at, c.created_at) DESC
                """, [uid, uid, uid] + params)
                return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


def _participant_where_pg(uid: str, role: str) -> Tuple[str, List]:
    role = role.upper()
    if role == "USER":
        return "c.user_id = %s", [uid]
    if role == "ADVOCATE":
        return "c.advocate_id = %s", [uid]
    return "1=1", []   # ADMIN sees all


def _sqlite_list_conversations(uid: str, role: str) -> List[Dict[str, Any]]:
    role = role.upper()
    with _sqlite_conn() as conn:
        if role == "USER":
            where = "c.user_id = ?"
        elif role == "ADVOCATE":
            where = "c.advocate_id = ?"
        else:
            where = "1=1"

        rows = conn.execute(f"""
            SELECT
                c.*,
                u.full_name AS other_party_name,
                u.avatar_url AS other_party_avatar,
                u.designation AS other_party_designation,
                m.body AS last_message_body,
                m.sender_id AS last_message_sender_id,
                (
                    SELECT COUNT(*) FROM chat_messages cm
                    WHERE cm.conversation_id = c.id
                      AND cm.sender_id != ?
                      AND cm.created_at > COALESCE(
                          (SELECT last_read_at FROM chat_participant_state
                           WHERE conversation_id = c.id AND user_id = ?),
                          '1970-01-01T00:00:00+00:00'
                      )
                ) AS unread_count
            FROM chat_conversations c
            LEFT JOIN users u ON u.id = (
                CASE WHEN c.user_id = ? THEN c.advocate_id ELSE c.user_id END
            )
            LEFT JOIN chat_messages m ON m.id = (
                SELECT id FROM chat_messages
                WHERE conversation_id = c.id
                ORDER BY created_at DESC, id DESC
                LIMIT 1
            )
            WHERE {where}
            ORDER BY COALESCE(c.last_message_at, c.created_at) DESC
        """, [uid, uid, uid, uid] if where != "1=1" else [uid, uid, uid]).fetchall()
        return [dict(r) for r in rows]


def get_conversation(
    conversation_id: str,
    current_user_id: str,
    current_user_role: str,
) -> Optional[Dict[str, Any]]:
    """Return conversation if the current user is a participant."""
    if is_postgres_authoritative():
        return _pg_get_conversation(conversation_id, current_user_id, current_user_role)
    return _sqlite_get_conversation(conversation_id, current_user_id, current_user_role)


def _pg_get_conversation(conv_id: str, uid: str, role: str) -> Optional[Dict[str, Any]]:
    import psycopg2.extras
    conn = get_pg_connection()
    try:
        with conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    """SELECT c.*,
                              u.full_name AS other_party_name,
                              u.avatar_url AS other_party_avatar,
                              u.designation AS other_party_designation,
                              u.role AS other_party_role
                       FROM public.chat_conversations c
                       LEFT JOIN public.users u ON u.id = (
                           CASE WHEN c.user_id = %s THEN c.advocate_id ELSE c.user_id END
                       )
                       WHERE c.id=%s""",
                    (uid, conv_id),
                )
                row = cur.fetchone()
                if not row:
                    return None
                if not _is_participant(dict(row), uid, role):
                    return None
                return dict(row)
    finally:
        conn.close()


def _sqlite_get_conversation(conv_id: str, uid: str, role: str) -> Optional[Dict[str, Any]]:
    with _sqlite_conn() as conn:
        row = conn.execute(
            """SELECT c.*,
                      u.full_name AS other_party_name,
                      u.avatar_url AS other_party_avatar,
                      u.designation AS other_party_designation,
                      u.role AS other_party_role
               FROM chat_conversations c
               LEFT JOIN users u ON u.id = (
                   CASE WHEN c.user_id = ? THEN c.advocate_id ELSE c.user_id END
               )
               WHERE c.id=?""",
            (uid, conv_id),
        ).fetchone()
        if not row:
            return None
        d = dict(row)
        if not _is_participant(d, uid, role):
            return None
        return d


def _is_participant(conv: Dict[str, Any], uid: str, role: str) -> bool:
    role = role.upper()
    if role == "ADMIN":
        return True
    if role == "USER":
        return conv.get("user_id") == uid
    if role == "ADVOCATE":
        return conv.get("advocate_id") == uid
    return False


# ── Message operations ─────────────────────────────────────────────────────────

def create_message(
    conversation_id: str,
    sender_id: str,
    body: Optional[str],
    idempotency_key: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Persist a chat message.
    The caller must already have verified conversation participant access.
    Returns the persisted message dict.
    Raises ValueError for invalid/empty content.
    """
    body_clean = (body or "").strip()
    if not body_clean:
        raise ValueError("Message body cannot be empty.")
    if len(body_clean) > MAX_MESSAGE_BODY_LEN:
        raise ValueError(f"Message exceeds maximum length of {MAX_MESSAGE_BODY_LEN} characters.")

    msg_id = str(uuid.uuid4())
    now = _utcnow()

    if is_postgres_authoritative():
        return _pg_create_message(msg_id, conversation_id, sender_id, body_clean, idempotency_key, now)
    return _sqlite_create_message(msg_id, conversation_id, sender_id, body_clean, idempotency_key, now)


def _pg_create_message(
    msg_id: str, conv_id: str, sender_id: str, body: str,
    ikey: Optional[str], now: str
) -> Dict[str, Any]:
    import psycopg2.extras
    conn = get_pg_connection()
    try:
        with conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    """INSERT INTO public.chat_messages
                       (id, conversation_id, sender_id, body, idempotency_key, created_at)
                       VALUES (%s,%s,%s,%s,%s,%s)
                       ON CONFLICT (conversation_id, idempotency_key) DO UPDATE
                           SET body = EXCLUDED.body
                       RETURNING *""",
                    (msg_id, conv_id, sender_id, body, ikey, now),
                )
                msg = dict(cur.fetchone())
                cur.execute(
                    """UPDATE public.chat_conversations
                       SET last_message_at=%s, updated_at=%s
                       WHERE id=%s""",
                    (now, now, conv_id),
                )
                return msg
    finally:
        conn.close()


def _sqlite_create_message(
    msg_id: str, conv_id: str, sender_id: str, body: str,
    ikey: Optional[str], now: str
) -> Dict[str, Any]:
    with _sqlite_conn() as conn:
        try:
            conn.execute(
                """INSERT INTO chat_messages
                   (id, conversation_id, sender_id, body, idempotency_key, created_at)
                   VALUES (?,?,?,?,?,?)""",
                (msg_id, conv_id, sender_id, body, ikey, now),
            )
        except sqlite3.IntegrityError:
            # Idempotency: return existing message with same key
            if ikey:
                row = conn.execute(
                    "SELECT * FROM chat_messages WHERE conversation_id=? AND idempotency_key=?",
                    (conv_id, ikey),
                ).fetchone()
                if row:
                    return dict(row)
            raise
        conn.execute(
            "UPDATE chat_conversations SET last_message_at=?, updated_at=? WHERE id=?",
            (now, now, conv_id),
        )
        return dict(conn.execute(
            "SELECT * FROM chat_messages WHERE id=?", (msg_id,)
        ).fetchone())


def list_messages(
    conversation_id: str,
    before_created_at: Optional[str] = None,
    before_id: Optional[str] = None,
    limit: int = 30,
) -> List[Dict[str, Any]]:
    """
    Paginated message history for a conversation.
    Cursor = (before_created_at, before_id) — returns messages older than the cursor.
    Results are returned oldest-first within each page for display chronology.
    """
    limit = min(max(limit, 1), 100)
    if is_postgres_authoritative():
        return _pg_list_messages(conversation_id, before_created_at, before_id, limit)
    return _sqlite_list_messages(conversation_id, before_created_at, before_id, limit)


def _pg_list_messages(
    conv_id: str, before_ts: Optional[str], before_id: Optional[str], limit: int
) -> List[Dict[str, Any]]:
    import psycopg2.extras
    conn = get_pg_connection()
    try:
        with conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                if before_ts and before_id:
                    cur.execute(
                        """SELECT * FROM public.chat_messages
                           WHERE conversation_id=%s
                             AND (created_at, id) < (%s, %s)
                           ORDER BY created_at DESC, id DESC
                           LIMIT %s""",
                        (conv_id, before_ts, before_id, limit),
                    )
                else:
                    cur.execute(
                        """SELECT * FROM public.chat_messages
                           WHERE conversation_id=%s
                           ORDER BY created_at DESC, id DESC
                           LIMIT %s""",
                        (conv_id, limit),
                    )
                rows = [dict(r) for r in cur.fetchall()]
                return list(reversed(rows))  # chronological for display
    finally:
        conn.close()


def _sqlite_list_messages(
    conv_id: str, before_ts: Optional[str], before_id: Optional[str], limit: int
) -> List[Dict[str, Any]]:
    with _sqlite_conn() as conn:
        if before_ts and before_id:
            rows = conn.execute(
                """SELECT * FROM chat_messages
                   WHERE conversation_id=?
                     AND (created_at < ? OR (created_at = ? AND id < ?))
                   ORDER BY created_at DESC, id DESC
                   LIMIT ?""",
                (conv_id, before_ts, before_ts, before_id, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                """SELECT * FROM chat_messages
                   WHERE conversation_id=?
                   ORDER BY created_at DESC, id DESC
                   LIMIT ?""",
                (conv_id, limit),
            ).fetchall()
        return list(reversed([dict(r) for r in rows]))


# ── Attachment operations ──────────────────────────────────────────────────────

def create_attachment(
    message_id: str,
    conversation_id: str,
    uploaded_by: str,
    storage_key: str,
    original_filename: str,
    content_type: Optional[str],
    size_bytes: int,
) -> Dict[str, Any]:
    att_id = str(uuid.uuid4())
    now = _utcnow()
    if is_postgres_authoritative():
        return _pg_create_attachment(
            att_id, message_id, conversation_id, uploaded_by,
            storage_key, original_filename, content_type, size_bytes, now
        )
    return _sqlite_create_attachment(
        att_id, message_id, conversation_id, uploaded_by,
        storage_key, original_filename, content_type, size_bytes, now
    )


def _pg_create_attachment(att_id, msg_id, conv_id, by_, skey, fname, ctype, size, now):
    import psycopg2.extras
    conn = get_pg_connection()
    try:
        with conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    """INSERT INTO public.chat_attachments
                       (id,message_id,conversation_id,uploaded_by,storage_key,
                        original_filename,content_type,size_bytes,created_at)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING *""",
                    (att_id, msg_id, conv_id, by_, skey, fname, ctype, size, now),
                )
                return dict(cur.fetchone())
    finally:
        conn.close()


def _sqlite_create_attachment(att_id, msg_id, conv_id, by_, skey, fname, ctype, size, now):
    with _sqlite_conn() as conn:
        conn.execute(
            """INSERT INTO chat_attachments
               (id,message_id,conversation_id,uploaded_by,storage_key,
                original_filename,content_type,size_bytes,created_at)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (att_id, msg_id, conv_id, by_, skey, fname, ctype, size, now),
        )
        return dict(conn.execute(
            "SELECT * FROM chat_attachments WHERE id=?", (att_id,)
        ).fetchone())


def get_attachment(attachment_id: str) -> Optional[Dict[str, Any]]:
    if is_postgres_authoritative():
        return _pg_get_attachment(attachment_id)
    return _sqlite_get_attachment(attachment_id)


def _pg_get_attachment(att_id: str) -> Optional[Dict[str, Any]]:
    import psycopg2.extras
    conn = get_pg_connection()
    try:
        with conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    "SELECT * FROM public.chat_attachments WHERE id=%s", (att_id,)
                )
                row = cur.fetchone()
                return dict(row) if row else None
    finally:
        conn.close()


def _sqlite_get_attachment(att_id: str) -> Optional[Dict[str, Any]]:
    with _sqlite_conn() as conn:
        row = conn.execute(
            "SELECT * FROM chat_attachments WHERE id=?", (att_id,)
        ).fetchone()
        return dict(row) if row else None


def list_attachments_for_message(message_id: str) -> List[Dict[str, Any]]:
    if is_postgres_authoritative():
        return _pg_list_attachments_for_message(message_id)
    return _sqlite_list_attachments_for_message(message_id)


def _pg_list_attachments_for_message(msg_id: str) -> List[Dict[str, Any]]:
    import psycopg2.extras
    conn = get_pg_connection()
    try:
        with conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    "SELECT * FROM public.chat_attachments WHERE message_id=%s ORDER BY created_at",
                    (msg_id,),
                )
                return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


def _sqlite_list_attachments_for_message(msg_id: str) -> List[Dict[str, Any]]:
    with _sqlite_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM chat_attachments WHERE message_id=? ORDER BY created_at",
            (msg_id,),
        ).fetchall()
        return [dict(r) for r in rows]


# ── Read-state operations ──────────────────────────────────────────────────────

def update_read_state(
    conversation_id: str,
    user_id: str,
    last_read_message_id: str,
) -> None:
    """Mark a participant's last-read position."""
    now = _utcnow()
    if is_postgres_authoritative():
        _pg_update_read_state(conversation_id, user_id, last_read_message_id, now)
    else:
        _sqlite_update_read_state(conversation_id, user_id, last_read_message_id, now)


def _pg_update_read_state(conv_id, uid, msg_id, now):
    conn = get_pg_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO public.chat_participant_state
                       (conversation_id, user_id, last_read_message_id, last_read_at, updated_at)
                       VALUES (%s,%s,%s,%s,%s)
                       ON CONFLICT (conversation_id, user_id) DO UPDATE
                           SET last_read_message_id=EXCLUDED.last_read_message_id,
                               last_read_at=EXCLUDED.last_read_at,
                               updated_at=EXCLUDED.updated_at""",
                    (conv_id, uid, msg_id, now, now),
                )
    finally:
        conn.close()


def _sqlite_update_read_state(conv_id, uid, msg_id, now):
    with _sqlite_conn() as conn:
        conn.execute(
            """INSERT INTO chat_participant_state
               (conversation_id, user_id, last_read_message_id, last_read_at, updated_at)
               VALUES (?,?,?,?,?)
               ON CONFLICT(conversation_id, user_id) DO UPDATE
                   SET last_read_message_id=excluded.last_read_message_id,
                       last_read_at=excluded.last_read_at,
                       updated_at=excluded.updated_at""",
            (conv_id, uid, msg_id, now, now),
        )


def get_unread_count(conversation_id: str, user_id: str) -> int:
    """Count messages in conversation not sent by user_id and newer than their last read."""
    if is_postgres_authoritative():
        return _pg_get_unread_count(conversation_id, user_id)
    return _sqlite_get_unread_count(conversation_id, user_id)


def _pg_get_unread_count(conv_id: str, uid: str) -> int:
    conn = get_pg_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """SELECT COUNT(*) FROM public.chat_messages
                       WHERE conversation_id=%s
                         AND sender_id != %s
                         AND created_at > COALESCE(
                             (SELECT last_read_at FROM public.chat_participant_state
                              WHERE conversation_id=%s AND user_id=%s),
                             '1970-01-01T00:00:00Z'
                         )""",
                    (conv_id, uid, conv_id, uid),
                )
                return cur.fetchone()[0]
    finally:
        conn.close()


def _sqlite_get_unread_count(conv_id: str, uid: str) -> int:
    with _sqlite_conn() as conn:
        row = conn.execute(
            """SELECT COUNT(*) FROM chat_messages
               WHERE conversation_id=?
                 AND sender_id != ?
                 AND created_at > COALESCE(
                     (SELECT last_read_at FROM chat_participant_state
                      WHERE conversation_id=? AND user_id=?),
                     '1970-01-01T00:00:00+00:00'
                 )""",
            (conv_id, uid, conv_id, uid),
        ).fetchone()
        return row[0] if row else 0
