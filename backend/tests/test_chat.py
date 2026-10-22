"""
NyayaSarathi Chat Feature — Authorization & Persistence Tests
Tests authorization enforcement, message persistence, pagination,
read-state, and idempotency using the SQLite fallback mode.

Run with: python -m pytest backend/tests/test_chat.py -v
or: cd backend && pytest tests/test_chat.py -v
"""

import os
import sys
import pytest

# Force SQLite mode for all tests
os.environ["NYAYASARATHI_USE_SQLITE"] = "1"

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.chat_repository import (
    init_chat_tables,
    get_or_create_conversation,
    create_message,
    list_messages,
    update_read_state,
    get_unread_count,
    list_conversations,
    get_conversation,
    create_attachment,
    get_attachment,
)
from services.user_repository import get_db_connection


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def setup_tables():
    """Initialize chat tables and seed test users before every test."""
    init_chat_tables()

    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    conn = get_db_connection()
    for uid, role, name in [
        ("u-test-001", "USER", "Alice User"),
        ("u-test-002", "USER", "Bob User"),
        ("a-test-001", "ADVOCATE", "Adv Alice"),
        ("a-test-002", "ADVOCATE", "Adv Bob"),
    ]:
        conn.execute(
            """INSERT OR IGNORE INTO users
               (id, email, password_hash, full_name, role, created_at, updated_at)
               VALUES (?,?,?,?,?,?,?)""",
            (uid, uid + "@test.com", "hash", name, role, now, now),
        )
    conn.commit()
    conn.close()
    yield


# ── Authorization tests ────────────────────────────────────────────────────────

class TestConversationAuth:

    def test_user_can_create_own_conversation(self):
        conv = get_or_create_conversation("u-test-001", "a-test-001", "u-test-001", "USER")
        assert conv["user_id"] == "u-test-001"
        assert conv["advocate_id"] == "a-test-001"

    def test_advocate_can_create_their_own_conversation(self):
        conv = get_or_create_conversation("u-test-001", "a-test-001", "a-test-001", "ADVOCATE")
        assert conv["advocate_id"] == "a-test-001"

    def test_user_cannot_create_conversation_for_other_user(self):
        """USER u-test-002 cannot create a conversation on behalf of u-test-001."""
        with pytest.raises(PermissionError):
            get_or_create_conversation("u-test-001", "a-test-001", "u-test-002", "USER")

    def test_advocate_cannot_create_conversation_for_other_advocate(self):
        """ADVOCATE a-test-002 cannot impersonate a-test-001."""
        with pytest.raises(PermissionError):
            get_or_create_conversation("u-test-001", "a-test-001", "a-test-002", "ADVOCATE")

    def test_same_user_and_advocate_rejected(self):
        with pytest.raises(ValueError):
            get_or_create_conversation("u-test-001", "u-test-001", "u-test-001", "USER")

    def test_idempotent_creation(self):
        """Creating the same pair twice returns the same conversation."""
        c1 = get_or_create_conversation("u-test-001", "a-test-001", "u-test-001", "USER")
        c2 = get_or_create_conversation("u-test-001", "a-test-001", "a-test-001", "ADVOCATE")
        assert c1["id"] == c2["id"]

    def test_user_cannot_access_other_conversation(self):
        """u-test-002 cannot see u-test-001's conversation."""
        conv = get_or_create_conversation("u-test-001", "a-test-001", "u-test-001", "USER")
        result = get_conversation(conv["id"], "u-test-002", "USER")
        assert result is None

    def test_advocate_cannot_access_other_conversation(self):
        """a-test-002 cannot see a-test-001's conversation."""
        conv = get_or_create_conversation("u-test-001", "a-test-001", "u-test-001", "USER")
        result = get_conversation(conv["id"], "a-test-002", "ADVOCATE")
        assert result is None

    def test_admin_can_access_any_conversation(self):
        """ADMIN can access any conversation."""
        conv = get_or_create_conversation("u-test-001", "a-test-001", "u-test-001", "USER")
        result = get_conversation(conv["id"], "admin-any", "ADMIN")
        assert result is not None
        assert result["id"] == conv["id"]

    def test_nonexistent_conversation_returns_none(self):
        result = get_conversation("nonexistent-id", "u-test-001", "USER")
        assert result is None


# ── Message tests ──────────────────────────────────────────────────────────────

class TestMessages:

    def _get_conv(self):
        return get_or_create_conversation("u-test-001", "a-test-001", "u-test-001", "USER")

    def test_create_message_persists(self):
        conv = self._get_conv()
        msg = create_message(conv["id"], "u-test-001", "Hello advocate!")
        assert msg["id"]
        assert msg["body"] == "Hello advocate!"
        assert msg["sender_id"] == "u-test-001"
        assert msg["conversation_id"] == conv["id"]

    def test_empty_message_rejected(self):
        conv = self._get_conv()
        with pytest.raises(ValueError):
            create_message(conv["id"], "u-test-001", "")

    def test_whitespace_only_message_rejected(self):
        conv = self._get_conv()
        with pytest.raises(ValueError):
            create_message(conv["id"], "u-test-001", "   \n\t  ")

    def test_overlong_message_rejected(self):
        conv = self._get_conv()
        with pytest.raises(ValueError):
            create_message(conv["id"], "u-test-001", "x" * 5000)

    def test_idempotency_key_deduplicates(self):
        conv = self._get_conv()
        ikey = "my-unique-key-123"
        m1 = create_message(conv["id"], "u-test-001", "First send", idempotency_key=ikey)
        m2 = create_message(conv["id"], "u-test-001", "First send", idempotency_key=ikey)
        assert m1["id"] == m2["id"]

    def test_message_list_chronological(self):
        conv = self._get_conv()
        for i in range(5):
            create_message(conv["id"], "u-test-001", f"Message {i}")
        msgs = list_messages(conv["id"])
        timestamps = [m["created_at"] for m in msgs]
        assert timestamps == sorted(timestamps)

    def test_pagination_limit(self):
        conv = self._get_conv()
        for i in range(10):
            create_message(conv["id"], "u-test-001", f"msg {i}")
        page = list_messages(conv["id"], limit=5)
        assert len(page) == 5

    def test_pagination_cursor_no_duplicates(self):
        conv = self._get_conv()
        for i in range(8):
            create_message(conv["id"], "u-test-001", f"page msg {i}")
        page1 = list_messages(conv["id"], limit=5)
        assert len(page1) >= 1
        oldest = page1[0]
        page2 = list_messages(
            conv["id"],
            before_created_at=oldest["created_at"],
            before_id=oldest["id"],
            limit=5,
        )
        ids_p1 = {m["id"] for m in page1}
        ids_p2 = {m["id"] for m in page2}
        assert not ids_p1.intersection(ids_p2), "Pages must not overlap"


# ── Read-state tests ───────────────────────────────────────────────────────────

class TestReadState:

    def _get_conv(self):
        return get_or_create_conversation("u-test-001", "a-test-001", "u-test-001", "USER")

    def test_unread_count_increments(self):
        conv = self._get_conv()
        create_message(conv["id"], "a-test-001", "Msg from advocate")
        unread = get_unread_count(conv["id"], "u-test-001")
        assert unread >= 1

    def test_mark_read_clears_unread(self):
        conv = self._get_conv()
        msg = create_message(conv["id"], "a-test-001", "Please read me")
        update_read_state(conv["id"], "u-test-001", msg["id"])
        unread = get_unread_count(conv["id"], "u-test-001")
        assert unread == 0

    def test_own_messages_do_not_count_as_unread(self):
        conv = self._get_conv()
        msg = create_message(conv["id"], "u-test-001", "My own message")
        # Unread from u-test-001's perspective: messages not sent by u-test-001
        unread = get_unread_count(conv["id"], "u-test-001")
        assert unread == 0


# ── Conversation list tests ────────────────────────────────────────────────────

class TestConversationList:

    def test_user_sees_own_conversations(self):
        get_or_create_conversation("u-test-001", "a-test-001", "u-test-001", "USER")
        convs = list_conversations("u-test-001", "USER")
        user_ids = [c["user_id"] for c in convs]
        assert all(uid == "u-test-001" for uid in user_ids)

    def test_user_does_not_see_other_conversations(self):
        get_or_create_conversation("u-test-002", "a-test-002", "u-test-002", "USER")
        convs = list_conversations("u-test-001", "USER")
        for c in convs:
            assert c["user_id"] == "u-test-001"

    def test_advocate_sees_their_conversations(self):
        get_or_create_conversation("u-test-001", "a-test-001", "u-test-001", "USER")
        convs = list_conversations("a-test-001", "ADVOCATE")
        adv_ids = [c["advocate_id"] for c in convs]
        assert all(aid == "a-test-001" for aid in adv_ids)


# ── Attachment metadata tests ─────────────────────────────────────────────────

class TestAttachments:

    def test_create_and_retrieve_attachment(self):
        conv = get_or_create_conversation("u-test-001", "a-test-001", "u-test-001", "USER")
        msg = create_message(conv["id"], "u-test-001", "[Attachment: test.pdf]")
        att = create_attachment(
            message_id=msg["id"],
            conversation_id=conv["id"],
            uploaded_by="u-test-001",
            storage_key="conv-x/u/uuid/test.pdf",
            original_filename="test.pdf",
            content_type="application/pdf",
            size_bytes=1024,
        )
        assert att["id"]
        fetched = get_attachment(att["id"])
        assert fetched is not None
        assert fetched["original_filename"] == "test.pdf"
        assert fetched["conversation_id"] == conv["id"]

    def test_nonexistent_attachment_returns_none(self):
        result = get_attachment("does-not-exist")
        assert result is None
