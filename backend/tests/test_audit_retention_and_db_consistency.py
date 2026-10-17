"""
NyayaSarathi Regression Tests:
1. Durable Role-Change Audit Retention (Survives User and Admin Deletion).
2. Authoritative Database Source-of-Truth & Transactional Consistency.
"""

import os
import sys
import unittest
import uuid
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from services.user_repository import (
    create_user,
    get_user_by_id,
    delete_user_by_id,
    update_user_role_with_audit,
    get_role_audit_history,
    count_role_audits,
    is_postgres_authoritative,
    get_db_connection,
    init_user_table,
)


class TestDurableAuditRetentionAndConsistency(unittest.TestCase):
    def setUp(self):
        init_user_table()
        self.suffix = uuid.uuid4().hex[:8]
        # Create test admin
        self.admin = create_user(
            email=f"admin_audit_{self.suffix}@nyayasarathi.in",
            password_hash="testhash123",
            full_name=f"Admin Auditor {self.suffix}",
            role="ADMIN",
        )
        # Create test target user
        self.target = create_user(
            email=f"target_user_{self.suffix}@nyayasarathi.in",
            password_hash="testhash123",
            full_name=f"Target User {self.suffix}",
            role="USER",
        )

    def tearDown(self):
        # Best effort cleanup
        try:
            delete_user_by_id(self.target["id"])
            delete_user_by_id(self.admin["id"])
        except Exception:
            pass

    def test_01_role_change_creates_audit_with_immutable_snapshots(self):
        """Verify role change captures target_email, actor_email, and actor_name snapshots."""
        res = update_user_role_with_audit(
            target_user_id=self.target["id"],
            actor_user_id=self.admin["id"],
            new_role="JUDGE",
            reason="Elevated for judicial docket",
        )
        self.assertIsNotNone(res)
        self.assertEqual(res["new_role"], "JUDGE")
        self.assertEqual(res["old_role"], "USER")
        self.assertEqual(res["target_email"], self.target["email"])
        self.assertEqual(res["actor_email"], self.admin["email"])
        self.assertEqual(res["actor_name"], self.admin["full_name"])

        # Query history
        history = get_role_audit_history(limit=10, target_user_id=self.target["id"])
        self.assertTrue(len(history) >= 1)
        record = history[0]
        self.assertEqual(record["target_email"], self.target["email"])
        self.assertEqual(record["actor_email"], self.admin["email"])
        self.assertEqual(record["actor_name"], self.admin["full_name"])

    def test_02_audit_survives_target_user_deletion(self):
        """CRITICAL: Deleting the target user must NOT delete role-change audit records."""
        # 1. Perform role change
        update_user_role_with_audit(
            target_user_id=self.target["id"],
            actor_user_id=self.admin["id"],
            new_role="JUDGE",
            reason="Pre-deletion promotion test",
        )
        initial_count = count_role_audits(target_user_id=self.target["id"])
        self.assertGreaterEqual(initial_count, 1)

        # 2. Delete the target user account
        deleted = delete_user_by_id(self.target["id"])
        self.assertTrue(deleted)
        self.assertIsNone(get_user_by_id(self.target["id"]))

        # 3. Verify audit record survived in database
        # Under ON DELETE SET NULL, target_user_id is now NULL, but record exists with snapshot
        all_audits = get_role_audit_history(limit=50)
        matching = [a for a in all_audits if a.get("target_email") == self.target["email"]]
        self.assertTrue(
            len(matching) >= 1,
            f"Audit record for {self.target['email']} was destroyed upon user deletion! Cascading deletion defect."
        )

        surviving_record = matching[0]
        self.assertEqual(surviving_record["target_email"], self.target["email"])
        self.assertEqual(surviving_record["actor_email"], self.admin["email"])
        self.assertEqual(surviving_record["old_role"], "USER")
        self.assertEqual(surviving_record["new_role"], "JUDGE")

    def test_03_audit_survives_actor_admin_deletion(self):
        """CRITICAL: Deleting the acting admin must NOT delete historical role-change records."""
        update_user_role_with_audit(
            target_user_id=self.target["id"],
            actor_user_id=self.admin["id"],
            new_role="JUDGE",
            reason="Admin deletion survival test",
        )

        # Delete acting admin
        deleted = delete_user_by_id(self.admin["id"])
        self.assertTrue(deleted)
        self.assertIsNone(get_user_by_id(self.admin["id"]))

        # Verify audit record survived and retained actor's historical snapshot name/email
        history = get_role_audit_history(limit=50, target_user_id=self.target["id"])
        self.assertTrue(len(history) >= 1)
        record = history[0]
        self.assertEqual(record["actor_name"], self.admin["full_name"])
        self.assertEqual(record["actor_email"], self.admin["email"])

    def test_04_authoritative_database_transactional_integrity(self):
        """Verify that updating a non-existent user raises an error and does not produce orphan audits."""
        fake_user_id = str(uuid.uuid4())
        initial_audit_count = count_role_audits()

        with self.assertRaises(Exception):
            update_user_role_with_audit(
                target_user_id=fake_user_id,
                actor_user_id=self.admin["id"],
                new_role="JUDGE",
                reason="Should fail atomically",
            )

        final_audit_count = count_role_audits()
        self.assertEqual(initial_audit_count, final_audit_count)

    def test_05_offline_sqlite_mode_fallback(self):
        """Verify repository behaves consistently in isolated SQLite mode when NYAYASARATHI_USE_SQLITE=1."""
        os.environ["NYAYASARATHI_USE_SQLITE"] = "1"
        try:
            self.assertFalse(is_postgres_authoritative())
            # Create user in SQLite
            sqlite_user = create_user(
                email=f"sqlite_user_{self.suffix}@nyayasarathi.in",
                password_hash="sqlitehash",
                full_name="SQLite Only User",
                role="USER",
            )
            # Promote in SQLite
            audit = update_user_role_with_audit(
                target_user_id=sqlite_user["id"],
                actor_user_id=self.admin["id"],
                new_role="JUDGE",
                reason="SQLite promotion",
            )
            self.assertIsNotNone(audit)
            self.assertEqual(audit["new_role"], "JUDGE")

            # Delete user in SQLite and verify audit survives
            deleted = delete_user_by_id(sqlite_user["id"])
            self.assertTrue(deleted)
            history = get_role_audit_history(limit=50)
            matching = [a for a in history if a.get("target_email") == sqlite_user["email"]]
            self.assertTrue(len(matching) >= 1)
        finally:
            del os.environ["NYAYASARATHI_USE_SQLITE"]


if __name__ == "__main__":
    unittest.main()
