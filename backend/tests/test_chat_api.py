"""
NyayaSarathi Chat API — Comprehensive Integration & Authorization Tests
Tests FastAPI /api/chat endpoints using TestClient:
- Authentication & RBAC (USER, ADVOCATE, ADMIN, anonymous, invalid tokens)
- Cross-conversation isolation (cannot read or send to other users' conversations)
- Idempotency key handling
- Message length and empty message validation
- Pagination and cursors
- Read-state tracking and unread counts
- Attachment upload validation (MIME, extension, size limits) and authorized download
"""

import io
import os
import sys
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

# Use SQLite mode for local deterministic automated testing
os.environ["NYAYASARATHI_USE_SQLITE"] = "1"
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from main import app
from services.auth_service import create_access_token
from services.chat_repository import init_chat_tables
from services.user_repository import get_db_connection

client = TestClient(app)

USER_1_ID = "test-user-alice-01"
USER_2_ID = "test-user-bob-02"
ADVOCATE_1_ID = "test-adv-priya-01"
ADVOCATE_2_ID = "test-adv-rohan-02"
ADMIN_ID = "test-admin-sys-01"


@pytest.fixture(scope="module", autouse=True)
def setup_test_environment():
    """Seed test users into SQLite DB and create chat tables."""
    init_chat_tables()
    conn = get_db_connection()
    now = datetime.now(timezone.utc).isoformat()
    test_users = [
        (USER_1_ID, "alice@example.com", "Alice User", "USER"),
        (USER_2_ID, "bob@example.com", "Bob User", "USER"),
        (ADVOCATE_1_ID, "priya@example.com", "Adv. Priya", "ADVOCATE"),
        (ADVOCATE_2_ID, "rohan@example.com", "Adv. Rohan", "ADVOCATE"),
        (ADMIN_ID, "admin@example.com", "Admin Judicial", "ADMIN"),
    ]
    for uid, email, name, role in test_users:
        conn.execute(
            """INSERT OR IGNORE INTO users
               (id, email, password_hash, full_name, role, created_at, updated_at)
               VALUES (?, ?, 'dummy_hash', ?, ?, ?, ?)""",
            (uid, email, name, role, now, now),
        )
    conn.commit()
    conn.close()


def auth_headers(uid: str, role: str, email: str = "test@example.com"):
    token = create_access_token(user_id=uid, email=email, role=role, full_name=uid)
    return {"Authorization": f"Bearer {token}"}


def get_error(res):
    body = res.json()
    return body.get("error") or body.get("detail") or str(body)


# ── 1. Authentication & RBAC Tests ─────────────────────────────────────────────

def test_unauthenticated_requests_rejected():
    res = client.get("/api/chat/conversations")
    assert res.status_code == 401

    res = client.post("/api/chat/conversations", json={"user_id": USER_1_ID, "advocate_id": ADVOCATE_1_ID})
    assert res.status_code == 401

    res = client.get("/api/chat/conversations/nonexistent/messages")
    assert res.status_code == 401


def test_invalid_token_rejected():
    res = client.get("/api/chat/conversations", headers={"Authorization": "Bearer invalid.token.value"})
    assert res.status_code == 401


def test_user_cannot_create_conversation_for_another_user():
    headers = auth_headers(USER_1_ID, "USER")
    res = client.post(
        "/api/chat/conversations",
        json={"user_id": USER_2_ID, "advocate_id": ADVOCATE_1_ID},
        headers=headers,
    )
    assert res.status_code == 403
    assert "USER can only create conversations for themselves" in get_error(res)


def test_advocate_cannot_create_conversation_for_another_advocate():
    headers = auth_headers(ADVOCATE_1_ID, "ADVOCATE")
    res = client.post(
        "/api/chat/conversations",
        json={"user_id": USER_1_ID, "advocate_id": ADVOCATE_2_ID},
        headers=headers,
    )
    assert res.status_code == 403
    assert "ADVOCATE can only participate in their own conversations" in get_error(res)


# ── 2. Conversation Lifecycle & Isolation ──────────────────────────────────────

def test_create_and_get_conversation_idempotent():
    headers = auth_headers(USER_1_ID, "USER")
    res1 = client.post(
        "/api/chat/conversations",
        json={"user_id": USER_1_ID, "advocate_id": ADVOCATE_1_ID},
        headers=headers,
    )
    assert res1.status_code == 201
    conv = res1.json()
    assert conv["user_id"] == USER_1_ID
    assert conv["advocate_id"] == ADVOCATE_1_ID
    conv_id = conv["id"]

    # Re-creating returns same conversation
    res2 = client.post(
        "/api/chat/conversations",
        json={"user_id": USER_1_ID, "advocate_id": ADVOCATE_1_ID},
        headers=headers,
    )
    assert res2.status_code == 201
    assert res2.json()["id"] == conv_id


def test_cross_conversation_isolation():
    u1_headers = auth_headers(USER_1_ID, "USER")
    res = client.post(
        "/api/chat/conversations",
        json={"user_id": USER_1_ID, "advocate_id": ADVOCATE_1_ID},
        headers=u1_headers,
    )
    conv_id = res.json()["id"]

    # User 2 tries to access User 1's conversation detail -> 404
    u2_headers = auth_headers(USER_2_ID, "USER")
    res_detail = client.get(f"/api/chat/conversations/{conv_id}", headers=u2_headers)
    assert res_detail.status_code == 404

    # User 2 tries to access User 1's conversation messages -> 404
    res_msgs = client.get(f"/api/chat/conversations/{conv_id}/messages", headers=u2_headers)
    assert res_msgs.status_code == 404

    # User 2 tries to send message to User 1's conversation -> 404
    res_send = client.post(
        f"/api/chat/conversations/{conv_id}/messages",
        json={"body": "Infiltration attempt"},
        headers=u2_headers,
    )
    assert res_send.status_code == 404


def test_admin_access_allowed():
    u1_headers = auth_headers(USER_1_ID, "USER")
    res = client.post(
        "/api/chat/conversations",
        json={"user_id": USER_1_ID, "advocate_id": ADVOCATE_1_ID},
        headers=u1_headers,
    )
    conv_id = res.json()["id"]

    admin_headers = auth_headers(ADMIN_ID, "ADMIN")
    res_admin = client.get(f"/api/chat/conversations/{conv_id}", headers=admin_headers)
    assert res_admin.status_code == 200
    assert res_admin.json()["id"] == conv_id


# ── 3. Messaging, Validation & Idempotency ─────────────────────────────────────

def test_send_and_paginate_messages():
    u1_headers = auth_headers(USER_1_ID, "USER")
    conv = client.post(
        "/api/chat/conversations",
        json={"user_id": USER_1_ID, "advocate_id": ADVOCATE_1_ID},
        headers=u1_headers,
    ).json()
    conv_id = conv["id"]

    # Send 3 messages
    m1 = client.post(f"/api/chat/conversations/{conv_id}/messages", json={"body": "Hello Adv. Priya"}, headers=u1_headers).json()
    m2 = client.post(f"/api/chat/conversations/{conv_id}/messages", json={"body": "Here are the facts of my case."}, headers=u1_headers).json()
    m3 = client.post(f"/api/chat/conversations/{conv_id}/messages", json={"body": "Please review at your earliest convenience."}, headers=u1_headers).json()

    assert m1["sender_id"] == USER_1_ID
    assert m2["sender_id"] == USER_1_ID
    assert m3["sender_id"] == USER_1_ID

    # Fetch messages
    res = client.get(f"/api/chat/conversations/{conv_id}/messages?limit=10", headers=u1_headers)
    assert res.status_code == 200
    data = res.json()
    assert len(data["messages"]) >= 3
    bodies = [m["body"] for m in data["messages"]]
    assert "Hello Adv. Priya" in bodies
    assert "Please review at your earliest convenience." in bodies


def test_empty_or_overlong_messages_rejected():
    u1_headers = auth_headers(USER_1_ID, "USER")
    conv = client.post(
        "/api/chat/conversations",
        json={"user_id": USER_1_ID, "advocate_id": ADVOCATE_1_ID},
        headers=u1_headers,
    ).json()
    conv_id = conv["id"]

    # Empty string
    r1 = client.post(f"/api/chat/conversations/{conv_id}/messages", json={"body": ""}, headers=u1_headers)
    assert r1.status_code in [422, 400]

    # Whitespace only
    r2 = client.post(f"/api/chat/conversations/{conv_id}/messages", json={"body": "   \n\t  "}, headers=u1_headers)
    assert r2.status_code in [422, 400]

    # Overlong message (> 4000 chars)
    r3 = client.post(f"/api/chat/conversations/{conv_id}/messages", json={"body": "A" * 4001}, headers=u1_headers)
    assert r3.status_code in [422, 400]


def test_idempotency_key_prevents_duplicate_sends():
    u1_headers = auth_headers(USER_1_ID, "USER")
    conv = client.post(
        "/api/chat/conversations",
        json={"user_id": USER_1_ID, "advocate_id": ADVOCATE_1_ID},
        headers=u1_headers,
    ).json()
    conv_id = conv["id"]

    key = "idem-key-unique-12345"
    payload = {"body": "Idempotent payment notification", "idempotency_key": key}

    r1 = client.post(f"/api/chat/conversations/{conv_id}/messages", json=payload, headers=u1_headers)
    assert r1.status_code == 201
    msg1 = r1.json()

    # Repeat with same key
    r2 = client.post(f"/api/chat/conversations/{conv_id}/messages", json=payload, headers=u1_headers)
    assert r2.status_code == 201
    msg2 = r2.json()

    assert msg1["id"] == msg2["id"]


# ── 4. Read State & Unread Counts ──────────────────────────────────────────────

def test_read_state_and_unread_counts():
    u1_headers = auth_headers(USER_1_ID, "USER")
    adv_headers = auth_headers(ADVOCATE_1_ID, "ADVOCATE")

    conv = client.post(
        "/api/chat/conversations",
        json={"user_id": USER_1_ID, "advocate_id": ADVOCATE_1_ID},
        headers=u1_headers,
    ).json()
    conv_id = conv["id"]

    # User sends a message
    msg = client.post(
        f"/api/chat/conversations/{conv_id}/messages",
        json={"body": "Notice of motion filed."},
        headers=u1_headers,
    ).json()

    # Advocate checks conversation detail -> unread count >= 1
    adv_detail = client.get(f"/api/chat/conversations/{conv_id}", headers=adv_headers).json()
    assert adv_detail["unread_count"] >= 1

    # Advocate marks as read
    mark_res = client.post(
        f"/api/chat/conversations/{conv_id}/read",
        json={"last_read_message_id": msg["id"]},
        headers=adv_headers,
    )
    assert mark_res.status_code == 200

    # Advocate checks again -> unread count is 0
    adv_detail_after = client.get(f"/api/chat/conversations/{conv_id}", headers=adv_headers).json()
    assert adv_detail_after["unread_count"] == 0


# ── 5. Attachment Validation & Authorization ───────────────────────────────────

def test_attachment_upload_disallowed_type():
    u1_headers = auth_headers(USER_1_ID, "USER")
    conv = client.post(
        "/api/chat/conversations",
        json={"user_id": USER_1_ID, "advocate_id": ADVOCATE_1_ID},
        headers=u1_headers,
    ).json()
    conv_id = conv["id"]

    # Disallowed .exe file
    file_data = io.BytesIO(b"MZ executable content")
    res = client.post(
        f"/api/chat/conversations/{conv_id}/attachments",
        files={"file": ("malware.exe", file_data, "application/octet-stream")},
        headers=u1_headers,
    )
    assert res.status_code == 422
    assert "not permitted" in get_error(res)


def test_attachment_upload_oversized():
    u1_headers = auth_headers(USER_1_ID, "USER")
    conv = client.post(
        "/api/chat/conversations",
        json={"user_id": USER_1_ID, "advocate_id": ADVOCATE_1_ID},
        headers=u1_headers,
    ).json()
    conv_id = conv["id"]

    # Exceeds 10MB limit (10MB + 1KB)
    oversized_data = io.BytesIO(b"0" * (10 * 1024 * 1024 + 1024))
    res = client.post(
        f"/api/chat/conversations/{conv_id}/attachments",
        files={"file": ("large_document.pdf", oversized_data, "application/pdf")},
        headers=u1_headers,
    )
    assert res.status_code == 413
    assert "exceeds maximum allowed size" in get_error(res)


def test_valid_attachment_upload_and_download_authorization():
    u1_headers = auth_headers(USER_1_ID, "USER")
    adv_headers = auth_headers(ADVOCATE_1_ID, "ADVOCATE")
    u2_headers = auth_headers(USER_2_ID, "USER")

    conv = client.post(
        "/api/chat/conversations",
        json={"user_id": USER_1_ID, "advocate_id": ADVOCATE_1_ID},
        headers=u1_headers,
    ).json()
    conv_id = conv["id"]

    # Upload valid text document
    file_bytes = b"Affidavit of Evidence sworn on 22 October 2026."
    file_data = io.BytesIO(file_bytes)
    res_upload = client.post(
        f"/api/chat/conversations/{conv_id}/attachments",
        files={"file": ("affidavit.txt", file_data, "text/plain")},
        headers=u1_headers,
    )
    assert res_upload.status_code == 201
    upload_json = res_upload.json()
    att_id = upload_json["attachment"]["id"]
    assert upload_json["attachment"]["original_filename"] == "affidavit.txt"
    assert "storage_key" not in upload_json["attachment"]

    # Authorized participant (Advocate) can download
    res_dl_adv = client.get(f"/api/chat/attachments/{att_id}", headers=adv_headers)
    assert res_dl_adv.status_code == 200
    assert res_dl_adv.content == file_bytes

    # Unrelated user (User 2) CANNOT download -> 404
    res_dl_u2 = client.get(f"/api/chat/attachments/{att_id}", headers=u2_headers)
    assert res_dl_u2.status_code == 404


def test_chat_health():
    res = client.get("/api/chat/health")
    assert res.status_code == 200
    data = res.json()
    assert "chat_db_mode" in data
    assert "realtime_available" in data


def test_advocate_directory_unauthenticated():
    res = client.get("/api/chat/advocates")
    assert res.status_code == 401


def test_advocate_directory_authenticated_and_safe_fields():
    u1_headers = auth_headers(USER_1_ID, "USER")
    res = client.get("/api/chat/advocates", headers=u1_headers)
    assert res.status_code == 200
    data = res.json()
    assert "advocates" in data
    assert "total" in data
    assert data["total"] >= 2
    for adv in data["advocates"]:
        assert adv["role"] == "ADVOCATE"
        assert "id" in adv
        assert "full_name" in adv
        assert "password_hash" not in adv
        assert "google_sub" not in adv


def test_create_conversation_rejects_non_advocate_target():
    u1_headers = auth_headers(USER_1_ID, "USER")
    # Attempt to pair USER_1 with USER_2 instead of an ADVOCATE
    res = client.post(
        "/api/chat/conversations",
        json={"user_id": USER_1_ID, "advocate_id": USER_2_ID},
        headers=u1_headers,
    )
    assert res.status_code == 422
    assert "must have role ADVOCATE" in get_error(res)


def test_conversations_list_enriches_other_party_name():
    u1_headers = auth_headers(USER_1_ID, "USER")
    adv_headers = auth_headers(ADVOCATE_1_ID, "ADVOCATE")

    # Ensure conversation exists
    client.post(
        "/api/chat/conversations",
        json={"user_id": USER_1_ID, "advocate_id": ADVOCATE_1_ID},
        headers=u1_headers,
    )

    # User 1 lists conversations: should see other_party_name == "Adv. Priya"
    res_u = client.get("/api/chat/conversations", headers=u1_headers)
    assert res_u.status_code == 200
    convs_u = res_u.json()["conversations"]
    target_u = [c for c in convs_u if c["advocate_id"] == ADVOCATE_1_ID][0]
    assert target_u["other_party_name"] == "Adv. Priya"

    # Advocate 1 lists conversations: should see other_party_name == "Alice User"
    res_a = client.get("/api/chat/conversations", headers=adv_headers)
    assert res_a.status_code == 200
    convs_a = res_a.json()["conversations"]
    target_a = [c for c in convs_a if c["user_id"] == USER_1_ID][0]
    assert target_a["other_party_name"] == "Alice User"

