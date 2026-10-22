"""
NyayaSarathi Chat API Router
Provides REST endpoints for the real-time User–Advocate chat feature.

All endpoints require authenticated JWT (get_current_user dependency).
Participant verification is enforced for every conversation, message,
read-state, and attachment operation.

Realtime delivery: After a successful message persist, the backend
publishes a minimal event to the Supabase Realtime channel for the
conversation (if Supabase is configured). The browser fetches the
full message from FastAPI after receiving the event.
In SQLite mode, Realtime is disabled; clients should poll via
GET /messages with a cursor instead of relying on push events.
"""

import os
import uuid
import secrets
import mimetypes
from pathlib import PurePosixPath
from typing import Any, Dict, List, Optional

from fastapi import (
    APIRouter, Depends, File, HTTPException, Query,
    UploadFile, status,
)
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, validator

from logger import get_logger
from services.auth_dependencies import get_current_user
from services.chat_repository import (
    MAX_MESSAGE_BODY_LEN,
    MAX_ATTACHMENT_BYTES,
    ALLOWED_EXTENSIONS,
    ALLOWED_MIME_TYPES,
    create_attachment,
    create_message,
    get_attachment,
    get_conversation,
    get_or_create_conversation,
    get_unread_count,
    init_chat_tables,
    list_attachments_for_message,
    list_conversations,
    list_messages,
    update_read_state,
)
from services.user_repository import is_postgres_authoritative

log = get_logger("nyayasarathi.chat_router")
router = APIRouter()

# Private Supabase storage bucket name — never hardcoded value, only env var ref.
CHAT_BUCKET = os.getenv("CHAT_STORAGE_BUCKET", "chat-attachments")


# ── Schema models ──────────────────────────────────────────────────────────────

class ConversationCreateRequest(BaseModel):
    user_id: str = Field(..., description="ID of the USER participant (TEXT, matches users.id)")
    advocate_id: str = Field(..., description="ID of the ADVOCATE participant (TEXT, matches users.id)")


class MessageSendRequest(BaseModel):
    body: str = Field(..., min_length=1, max_length=MAX_MESSAGE_BODY_LEN)
    idempotency_key: Optional[str] = Field(None, max_length=128)

    @validator("body")
    def strip_body(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Message body cannot be empty or whitespace.")
        return stripped


class ReadStateUpdateRequest(BaseModel):
    last_read_message_id: str


# ── Helpers ────────────────────────────────────────────────────────────────────

def _require_participant(
    conv_id: str, current_user: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Fetch conversation verifying participant access.
    Returns conversation dict or raises 403/404.
    """
    uid = current_user["id"]
    role = current_user.get("role", "USER")
    conv = get_conversation(conv_id, uid, role)
    if not conv:
        # Return 404 to avoid disclosing existence to non-participants
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found.",
        )
    return conv


def _safe_filename(name: str) -> str:
    """Strip path components and dangerous characters from an upload filename."""
    safe = PurePosixPath(name).name
    # Replace any remaining path separator
    return safe.replace("/", "_").replace("\\", "_")[:200]


def _publish_realtime_event(conversation_id: str, message_id: str, created_at: Any) -> None:
    """
    Publish a minimal event to the private Supabase Realtime channel for
    this conversation. Fires only after successful DB commit.
    Silently skips in SQLite mode or if Supabase is not configured.
    Payload intentionally omits message body, sender details, or tokens.
    """
    if not is_postgres_authoritative():
        log.debug(
            "SQLite mode: Supabase Realtime not available; skipping event publish.",
            extra={"component": "CHAT_ROUTER"},
        )
        return

    try:
        from services.supabase_client import get_supabase_client
        sb = get_supabase_client()
        if not sb:
            return
        channel_name = f"chat:{conversation_id}"
        # Use Supabase Realtime broadcast channel — server-side publish
        # The browser listens on this channel name after receiving a token.
        sb.channel(channel_name).send_broadcast(  # type: ignore[attr-defined]
            "new_message",
            {
                "type": "new_message",
                "conversation_id": conversation_id,
                "message_id": message_id,
                "created_at": str(created_at),
            },
        )
        log.debug(
            f"Published Realtime event for conversation {conversation_id} msg {message_id}",
            extra={"component": "CHAT_ROUTER"},
        )
    except Exception as exc:
        # Event publication failure must NOT roll back the persisted message.
        log.warning(
            f"Realtime event publish failed (non-fatal): {exc}",
            extra={"component": "CHAT_ROUTER"},
        )


# ── Endpoints ──────────────────────────────────────────────────────────────────

# GET /api/chat/conversations
@router.get("/conversations", tags=["Chat"])
async def list_my_conversations(
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Return all conversations accessible by the authenticated user.
    Includes unread count and last-message preview (body only, no attachments).
    """
    uid = current_user["id"]
    role = current_user.get("role", "USER")
    convs = list_conversations(uid, role)
    return {"conversations": convs, "total": len(convs)}


# POST /api/chat/conversations
@router.post("/conversations", status_code=status.HTTP_201_CREATED, tags=["Chat"])
async def create_or_get_conversation(
    payload: ConversationCreateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Idempotently create or retrieve a private conversation between
    a USER and an ADVOCATE. Role pairing and participant identity
    are verified server-side.
    """
    uid = current_user["id"]
    role = current_user.get("role", "USER")
    try:
        conv = get_or_create_conversation(
            user_id=payload.user_id,
            advocate_id=payload.advocate_id,
            current_user_id=uid,
            current_user_role=role,
        )
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    return conv


# GET /api/chat/conversations/{conversation_id}
@router.get("/conversations/{conversation_id}", tags=["Chat"])
async def get_conversation_detail(
    conversation_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Return conversation metadata after participant authorization."""
    conv = _require_participant(conversation_id, current_user)
    uid = current_user["id"]
    unread = get_unread_count(conversation_id, uid)
    return {**conv, "unread_count": unread}


# GET /api/chat/conversations/{conversation_id}/messages
@router.get("/conversations/{conversation_id}/messages", tags=["Chat"])
async def get_messages(
    conversation_id: str,
    before_created_at: Optional[str] = Query(None, description="ISO8601 timestamp cursor"),
    before_id: Optional[str] = Query(None, description="Message ID cursor"),
    limit: int = Query(30, ge=1, le=100),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Paginated message history, newest-first pagination with stable (timestamp, id) cursor.
    Returns messages in chronological order within each page.
    Participant access is verified before any content is returned.
    """
    _require_participant(conversation_id, current_user)
    msgs = list_messages(conversation_id, before_created_at, before_id, limit)

    # Attach attachments to each message
    enriched = []
    for m in msgs:
        attachments = list_attachments_for_message(m["id"])
        # Strip storage_key from client response — never expose internal paths
        safe_attachments = [
            {k: v for k, v in a.items() if k != "storage_key"}
            for a in attachments
        ]
        enriched.append({**m, "attachments": safe_attachments})

    # Provide next-page cursor
    next_cursor = None
    if enriched:
        oldest = enriched[0]
        next_cursor = {"before_created_at": oldest["created_at"], "before_id": oldest["id"]}

    return {
        "messages": enriched,
        "next_cursor": next_cursor,
        "has_more": len(msgs) == limit,
    }


# POST /api/chat/conversations/{conversation_id}/messages
@router.post(
    "/conversations/{conversation_id}/messages",
    status_code=status.HTTP_201_CREATED,
    tags=["Chat"],
)
async def send_message(
    conversation_id: str,
    payload: MessageSendRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Send a text message. Sender ID is derived exclusively from the verified JWT;
    request body cannot override it.
    Publishes a minimal Realtime event after successful persistence.
    """
    _require_participant(conversation_id, current_user)
    sender_id = current_user["id"]

    try:
        msg = create_message(
            conversation_id=conversation_id,
            sender_id=sender_id,
            body=payload.body,
            idempotency_key=payload.idempotency_key,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))

    # Publish event AFTER commit — non-fatal if it fails
    _publish_realtime_event(conversation_id, msg["id"], msg.get("created_at"))

    return msg


# POST /api/chat/conversations/{conversation_id}/read
@router.post("/conversations/{conversation_id}/read", tags=["Chat"])
async def mark_read(
    conversation_id: str,
    payload: ReadStateUpdateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Update the authenticated participant's read cursor."""
    _require_participant(conversation_id, current_user)
    uid = current_user["id"]
    update_read_state(conversation_id, uid, payload.last_read_message_id)
    return {"ok": True}


# POST /api/chat/conversations/{conversation_id}/attachments
@router.post(
    "/conversations/{conversation_id}/attachments",
    status_code=status.HTTP_201_CREATED,
    tags=["Chat"],
)
async def upload_attachment(
    conversation_id: str,
    file: UploadFile = File(...),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Upload a file attachment for a conversation.
    Validates size, extension, and MIME type server-side.
    Stores file in a private Supabase Storage bucket.
    In SQLite mode, local file storage is used (dev only).
    Returns attachment metadata (storage_key is not included in response).
    """
    conv = _require_participant(conversation_id, current_user)
    uid = current_user["id"]

    # ── 1. Size validation ────────────────────────────────────────────────────
    content = await file.read()
    if len(content) > MAX_ATTACHMENT_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of {MAX_ATTACHMENT_BYTES // (1024*1024)} MB.",
        )
    if len(content) == 0:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Empty file.")

    # ── 2. Extension + MIME validation ────────────────────────────────────────
    raw_name = file.filename or "upload"
    safe_name = _safe_filename(raw_name)
    ext = os.path.splitext(safe_name)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"File type '{ext}' is not permitted. Allowed: {sorted(ALLOWED_EXTENSIONS)}",
        )
    # Detect MIME from extension (do not trust browser-supplied content_type alone)
    detected_mime = mimetypes.guess_type(safe_name)[0]
    effective_mime = detected_mime if detected_mime in ALLOWED_MIME_TYPES else "application/octet-stream"

    # ── 3. Generate opaque storage key ───────────────────────────────────────
    storage_key = f"{conversation_id}/{uid}/{uuid.uuid4().hex}/{safe_name}"

    # ── 4. Store file ─────────────────────────────────────────────────────────
    if is_postgres_authoritative():
        _store_supabase(storage_key, content, effective_mime)
    else:
        _store_local(storage_key, content)

    # ── 5. Create placeholder message + attachment metadata ───────────────────
    # Attachment-only message — body uses a placeholder to satisfy not-null
    msg_body = f"[Attachment: {safe_name}]"
    msg = create_message(
        conversation_id=conversation_id,
        sender_id=uid,
        body=msg_body,
    )
    att = create_attachment(
        message_id=msg["id"],
        conversation_id=conversation_id,
        uploaded_by=uid,
        storage_key=storage_key,
        original_filename=safe_name,
        content_type=effective_mime,
        size_bytes=len(content),
    )

    # Publish Realtime event after successful persist
    _publish_realtime_event(conversation_id, msg["id"], msg.get("created_at"))

    safe_att = {k: v for k, v in att.items() if k != "storage_key"}
    return {**msg, "attachment": safe_att}


def _store_supabase(storage_key: str, content: bytes, mime: str) -> None:
    """Upload file bytes to the private Supabase Storage bucket."""
    try:
        from services.supabase_client import get_supabase_client
        sb = get_supabase_client()
        if not sb:
            raise RuntimeError("Supabase client unavailable.")
        sb.storage.from_(CHAT_BUCKET).upload(
            path=storage_key,
            file=content,
            file_options={"content-type": mime, "upsert": "false"},
        )
    except Exception as exc:
        log.error(f"Supabase storage upload failed: {exc}", extra={"component": "CHAT_ROUTER"})
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="File storage is temporarily unavailable.",
        )


def _store_local(storage_key: str, content: bytes) -> None:
    """
    Local dev fallback: store file on disk under backend/data/chat_uploads/.
    Not intended for production. Files are not encrypted at rest locally.
    """
    from pathlib import Path
    base = Path(__file__).parent.parent / "data" / "chat_uploads"
    dest = base / storage_key
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(content)


# GET /api/chat/attachments/{attachment_id}
@router.get("/attachments/{attachment_id}", tags=["Chat"])
async def download_attachment(
    attachment_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Authorize and download an attachment.
    In PostgreSQL mode: returns a short-lived signed Supabase Storage URL (redirect).
    In SQLite mode: streams file from local disk.
    storage_key is never exposed to the client.
    """
    att = get_attachment(attachment_id)
    if not att:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found.")

    # Verify participant access via conversation
    conv = _require_participant(att["conversation_id"], current_user)

    storage_key = att["storage_key"]
    safe_name = att.get("original_filename", "download")
    mime = att.get("content_type", "application/octet-stream")

    if is_postgres_authoritative():
        return _serve_supabase(storage_key, safe_name)
    return _serve_local(storage_key, safe_name, mime)


def _serve_supabase(storage_key: str, filename: str):
    """Issue a short-lived (60s) signed Supabase Storage URL and redirect."""
    from fastapi.responses import RedirectResponse
    try:
        from services.supabase_client import get_supabase_client
        sb = get_supabase_client()
        if not sb:
            raise RuntimeError("Supabase client unavailable.")
        result = sb.storage.from_(CHAT_BUCKET).create_signed_url(
            path=storage_key, expires_in=60
        )
        signed_url = result.get("signedURL") or result.get("signed_url")
        if not signed_url:
            raise RuntimeError("No signed URL returned by Supabase.")
        # Never log the signed URL — it is a short-lived credential
        return RedirectResponse(url=signed_url, status_code=302)
    except Exception as exc:
        log.error(f"Supabase signed URL generation failed: {exc}", extra={"component": "CHAT_ROUTER"})
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="File download is temporarily unavailable.",
        )


def _serve_local(storage_key: str, filename: str, mime: str):
    """Stream local file from disk (SQLite dev mode only)."""
    from pathlib import Path
    base = Path(__file__).parent.parent / "data" / "chat_uploads"
    dest = base / storage_key
    if not dest.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found on disk.")

    def _iter():
        with dest.open("rb") as f:
            while chunk := f.read(65536):
                yield chunk

    return StreamingResponse(
        _iter(),
        media_type=mime,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


# GET /api/chat/health (debug/mode indicator — no secrets)
@router.get("/health", tags=["Chat"])
async def chat_health():
    """
    Returns which database mode is active for chat (no sensitive info).
    """
    mode = "postgresql" if is_postgres_authoritative() else "sqlite"
    realtime_available = is_postgres_authoritative()
    return {
        "chat_db_mode": mode,
        "realtime_available": realtime_available,
        "realtime_note": (
            "Supabase Realtime is active in PostgreSQL mode."
            if realtime_available
            else "SQLite mode: Realtime is disabled. Use polling via GET /messages?before_* cursor."
        ),
    }
