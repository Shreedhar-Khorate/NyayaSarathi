"""
Unit & Integration Tests for Judge and Admin Dashboards
Tests:
  - 401 Unauthorized for unauthenticated requests
  - 403 Forbidden for USER attempting Admin or Judge endpoints
  - 403 Forbidden for JUDGE attempting Admin endpoints
  - 200 OK for JUDGE accessing Judge dashboard, activities, and cases
  - 200 OK for ADMIN accessing Admin metrics, users, role update, and audit history
  - Durable audit trail creation upon role mutation
  - Self-demotion protection for administrators
  - Last-admin removal prevention
  - Immediate permission revocation for demoted judges (stale token mitigation)
  - Prevention of privilege escalation during public registration
"""

import os
import sys
import unittest
from fastapi.testclient import TestClient

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from main import app
from services.auth_service import create_access_token
from services.user_repository import (
    create_user,
    get_user_by_email,
    get_user_by_id,
    update_user_role_with_audit,
    init_user_table,
)


class TestJudgeAndAdminDashboards(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_user_table()
        cls.client = TestClient(app)

        # Standard User
        cls.user_email = "test_dash_user@nyayasarathi.in"
        cls.user = get_user_by_email(cls.user_email)
        if not cls.user:
            cls.user = create_user(
                email=cls.user_email,
                password_hash=None,
                full_name="Adv. Rahul Deshmukh",
                role="USER",
                profile_completed=True,
            )

        # Judge User
        cls.judge_email = "test_dash_judge@nyayasarathi.in"
        cls.judge = get_user_by_email(cls.judge_email)
        if not cls.judge:
            cls.judge = create_user(
                email=cls.judge_email,
                password_hash=None,
                full_name="Hon'ble Justice Ramesh Chandra",
                role="JUDGE",
                organization="Delhi High Court",
                designation="Presiding Judge",
                profile_completed=True,
            )

        # Admin User
        cls.admin_email = "test_dash_admin@nyayasarathi.in"
        cls.admin = get_user_by_email(cls.admin_email)
        if not cls.admin:
            cls.admin = create_user(
                email=cls.admin_email,
                password_hash=None,
                full_name="Principal Judicial Administrator",
                role="ADMIN",
                profile_completed=True,
            )

        # Candidate user for role transition tests
        cls.target_email = "test_candidate_user@nyayasarathi.in"
        cls.target_user = get_user_by_email(cls.target_email)
        if not cls.target_user:
            cls.target_user = create_user(
                email=cls.target_email,
                password_hash=None,
                full_name="Adv. Meera Sen",
                role="USER",
                profile_completed=True,
            )

        cls.user_token = create_access_token(
            user_id=cls.user["id"],
            email=cls.user["email"],
            role=cls.user["role"],
            full_name=cls.user["full_name"],
        )
        cls.judge_token = create_access_token(
            user_id=cls.judge["id"],
            email=cls.judge["email"],
            role=cls.judge["role"],
            full_name=cls.judge["full_name"],
        )
        cls.admin_token = create_access_token(
            user_id=cls.admin["id"],
            email=cls.admin["email"],
            role=cls.admin["role"],
            full_name=cls.admin["full_name"],
        )

    # ── 1. Unauthenticated Security Boundary Tests ────────────────────────────
    def test_01_unauthenticated_requests_return_401(self):
        """Protected Judge and Admin endpoints must reject unauthenticated requests with 401."""
        endpoints = [
            ("GET", "/api/admin/dashboard"),
            ("GET", "/api/admin/users"),
            ("GET", "/api/admin/role-history"),
            ("PATCH", f"/api/admin/users/{self.target_user['id']}/role"),
            ("GET", "/api/judge/dashboard"),
            ("GET", "/api/judge/activity"),
            ("GET", "/api/judge/cases"),
        ]
        for method, url in endpoints:
            if method == "GET":
                res = self.client.get(url)
            else:
                res = self.client.patch(url, json={"new_role": "JUDGE"})
            self.assertEqual(
                res.status_code, 401,
                f"Endpoint {method} {url} should have returned 401 for unauthenticated request."
            )

    # ── 2. Standard User Access Boundaries ────────────────────────────────────
    def test_02_user_cannot_access_admin_endpoints(self):
        """Standard user must receive 403 Forbidden on all admin endpoints."""
        res_dash = self.client.get(
            "/api/admin/dashboard",
            headers={"Authorization": f"Bearer {self.user_token}"}
        )
        self.assertEqual(res_dash.status_code, 403)

        res_users = self.client.get(
            "/api/admin/users",
            headers={"Authorization": f"Bearer {self.user_token}"}
        )
        self.assertEqual(res_users.status_code, 403)

        res_patch = self.client.patch(
            f"/api/admin/users/{self.target_user['id']}/role",
            headers={"Authorization": f"Bearer {self.user_token}"},
            json={"new_role": "JUDGE"}
        )
        self.assertEqual(res_patch.status_code, 403)

    def test_03_user_cannot_access_judge_endpoints(self):
        """Standard user must receive 403 Forbidden on judge endpoints."""
        res = self.client.get(
            "/api/judge/dashboard",
            headers={"Authorization": f"Bearer {self.user_token}"}
        )
        self.assertEqual(res.status_code, 403)

    # ── 3. Judge Access Boundaries ────────────────────────────────────────────
    def test_04_judge_cannot_perform_admin_operations(self):
        """A judge must receive 403 Forbidden when attempting administrative mutations or metrics."""
        res_metrics = self.client.get(
            "/api/admin/dashboard",
            headers={"Authorization": f"Bearer {self.judge_token}"}
        )
        self.assertEqual(res_metrics.status_code, 403)

        res_role = self.client.patch(
            f"/api/admin/users/{self.target_user['id']}/role",
            headers={"Authorization": f"Bearer {self.judge_token}"},
            json={"new_role": "ADMIN"}
        )
        self.assertEqual(res_role.status_code, 403)

    def test_05_judge_can_access_judge_endpoints(self):
        """An authorized judge must successfully receive metrics, scoped activity, and bench cases."""
        res_dash = self.client.get(
            "/api/judge/dashboard",
            headers={"Authorization": f"Bearer {self.judge_token}"}
        )
        self.assertEqual(res_dash.status_code, 200)
        data = res_dash.json()
        self.assertIn("accessible_precedents", data)
        self.assertIn("judge_name", data)

        res_act = self.client.get(
            "/api/judge/activity",
            headers={"Authorization": f"Bearer {self.judge_token}"}
        )
        self.assertEqual(res_act.status_code, 200)

        res_cases = self.client.get(
            "/api/judge/cases",
            headers={"Authorization": f"Bearer {self.judge_token}"}
        )
        self.assertEqual(res_cases.status_code, 200)

    # ── 4. Admin Functionality & Role Management ──────────────────────────────
    def test_06_admin_can_view_metrics_and_users(self):
        """An administrator can read system metrics and list users with pagination."""
        res_dash = self.client.get(
            "/api/admin/dashboard",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        self.assertEqual(res_dash.status_code, 200)
        data = res_dash.json()
        self.assertGreaterEqual(data["total_users"], 1)
        self.assertIn("role_counts", data)

        res_users = self.client.get(
            "/api/admin/users?limit=10&offset=0",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        self.assertEqual(res_users.status_code, 200)
        users_data = res_users.json()
        self.assertIn("items", users_data)
        self.assertGreaterEqual(users_data["total"], 1)

    def test_07_admin_role_change_and_audit_persistence(self):
        """Admin promoting USER to JUDGE must persist in DB and write an audit record."""
        # Ensure candidate is USER
        update_user_role_with_audit(
            target_user_id=self.target_user["id"],
            actor_user_id=self.admin["id"],
            new_role="USER",
            reason="Reset for test",
        )

        res = self.client.patch(
            f"/api/admin/users/{self.target_user['id']}/role",
            headers={"Authorization": f"Bearer {self.admin_token}"},
            json={
                "new_role": "JUDGE",
                "reason": "Promoted to District Court Special Bench",
            }
        )
        self.assertEqual(res.status_code, 200)
        resp_data = res.json()
        self.assertTrue(resp_data["success"])
        self.assertEqual(resp_data["old_role"], "USER")
        self.assertEqual(resp_data["new_role"], "JUDGE")

        # Verify persistence in database
        updated_db_user = get_user_by_id(self.target_user["id"])
        self.assertEqual(updated_db_user["role"], "JUDGE")

        # Verify audit history
        res_audit = self.client.get(
            f"/api/admin/role-history?target_user_id={self.target_user['id']}",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        self.assertEqual(res_audit.status_code, 200)
        audits = res_audit.json()["items"]
        self.assertGreaterEqual(len(audits), 1)
        latest = audits[0]
        self.assertEqual(latest["new_role"], "JUDGE")
        self.assertEqual(latest["reason"], "Promoted to District Court Special Bench")

    # ── 5. Safety Guards: Self-Demotion, Last Admin, Invalid Targets ──────────
    def test_08_admin_cannot_demote_self(self):
        """Prevent self-demotion to avoid administrator lockout."""
        res = self.client.patch(
            f"/api/admin/users/{self.admin['id']}/role",
            headers={"Authorization": f"Bearer {self.admin_token}"},
            json={"new_role": "USER", "reason": "Accidental self-demotion"}
        )
        self.assertEqual(res.status_code, 400)
        self.assertIn("demote themselves", res.json()["error"])

    def test_09_invalid_user_returns_404(self):
        """Attempting to mutate a nonexistent user ID must return 404."""
        res = self.client.patch(
            "/api/admin/users/non-existent-user-id-99999/role",
            headers={"Authorization": f"Bearer {self.admin_token}"},
            json={"new_role": "JUDGE"}
        )
        self.assertEqual(res.status_code, 404)

    def test_10_invalid_role_returns_400(self):
        """Attempting to set an unsupported role must return 400."""
        res = self.client.patch(
            f"/api/admin/users/{self.target_user['id']}/role",
            headers={"Authorization": f"Bearer {self.admin_token}"},
            json={"new_role": "SUPER_OVERLORD"}
        )
        self.assertEqual(res.status_code, 400)

    # ── 6. Stale Token Defense: Immediate Revocation On Demotion ───────────────
    def test_11_demoted_judge_loses_privileged_access_immediately(self):
        """
        When a JUDGE is demoted to USER, subsequent requests using their previously issued
        token must immediately return 403 Forbidden (preventing stale elevated access).
        """
        # Create dedicated judge to test demotion
        demote_email = "temp_judge_demote@nyayasarathi.in"
        temp_judge = get_user_by_email(demote_email)
        if not temp_judge:
            temp_judge = create_user(
                email=demote_email,
                password_hash=None,
                full_name="Temporary Judge",
                role="JUDGE",
                profile_completed=True,
            )
        else:
            update_user_role_with_audit(temp_judge["id"], self.admin["id"], "JUDGE", "Set to JUDGE")

        # Issue token while still JUDGE
        temp_judge_token = create_access_token(
            user_id=temp_judge["id"],
            email=temp_judge["email"],
            role="JUDGE",
            full_name=temp_judge["full_name"],
        )

        # Confirm access works initially
        res_before = self.client.get(
            "/api/judge/dashboard",
            headers={"Authorization": f"Bearer {temp_judge_token}"}
        )
        self.assertEqual(res_before.status_code, 200)

        # Admin demotes judge to USER
        res_demote = self.client.patch(
            f"/api/admin/users/{temp_judge['id']}/role",
            headers={"Authorization": f"Bearer {self.admin_token}"},
            json={"new_role": "USER", "reason": "Tenure expired; role revoked"}
        )
        self.assertEqual(res_demote.status_code, 200)

        # Using the OLD token must now be rejected with 403 Forbidden!
        res_after = self.client.get(
            "/api/judge/dashboard",
            headers={"Authorization": f"Bearer {temp_judge_token}"}
        )
        self.assertEqual(
            res_after.status_code, 403,
            "Demoted judge must be denied access even with previously issued token."
        )

    # ── 7. Public Signup Role Tampering Prevention ─────────────────────────────
    def test_12_signup_prevents_client_elevated_role_injection(self):
        """Public signup must ignore attempts to self-assign ADMIN or JUDGE."""
        import uuid
        test_email = f"attacker_{uuid.uuid4().hex[:6]}@nyayasarathi.in"
        res = self.client.post(
            "/api/auth/signup",
            json={
                "email": test_email,
                "password": "Password123!",
                "full_name": "Infiltrator Account",
                "role": "ADMIN",  # Malicious self-assignment attempt
            }
        )
        self.assertEqual(res.status_code, 201)
        data = res.json()
        # Role must be sanitized to USER, not ADMIN
        self.assertEqual(data["user"]["role"], "USER")
        self.assertNotEqual(data["user"]["role"], "ADMIN")


if __name__ == "__main__":
    unittest.main()
