"""
Unit & Integration Tests for Role Governance and Admin Dashboard
Tests:
  - Strict 3-Role System (USER, ADVOCATE, ADMIN)
  - 401 Unauthorized for unauthenticated requests to protected endpoints
  - 403 Forbidden for USER attempting Admin endpoints
  - 403 Forbidden for ADVOCATE attempting Admin endpoints
  - 404 Not Found for removed /api/judge/* endpoints
  - 403 Forbidden for legacy JUDGE or DEACTIVATED_JUDGE accounts attempting login or token usage
  - 400 Bad Request when attempting to assign deprecated 'JUDGE' role via role management
  - 200 OK for ADMIN accessing Admin metrics, users, role update (promoting to ADVOCATE), and audit history
  - Durable audit trail creation upon role mutation (USER -> ADVOCATE)
  - Self-demotion protection for administrators
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
from services.auth_service import create_access_token, hash_password
from services.user_repository import (
    create_user,
    get_user_by_email,
    get_user_by_id,
    update_user_role_with_audit,
    init_user_table,
)


class TestRolesAndAdminDashboard(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_user_table()
        cls.client = TestClient(app)

        # Standard User
        cls.user_email = "test_roles_user@nyayasarathi.in"
        cls.user = get_user_by_email(cls.user_email)
        if not cls.user:
            cls.user = create_user(
                email=cls.user_email,
                password_hash=hash_password("UserPassword123!"),
                full_name="Citizen Rahul Deshmukh",
                role="USER",
                profile_completed=True,
            )

        # Advocate User
        cls.advocate_email = "test_roles_advocate@nyayasarathi.in"
        cls.advocate = get_user_by_email(cls.advocate_email)
        if not cls.advocate:
            cls.advocate = create_user(
                email=cls.advocate_email,
                password_hash=hash_password("AdvocatePassword123!"),
                full_name="Adv. Priya Sharma",
                role="ADVOCATE",
                organization="Delhi High Court Bar Association",
                designation="Senior Advocate",
                profile_completed=True,
            )

        # Admin User
        cls.admin_email = "test_roles_admin@nyayasarathi.in"
        cls.admin = get_user_by_email(cls.admin_email)
        if not cls.admin:
            cls.admin = create_user(
                email=cls.admin_email,
                password_hash=hash_password("AdminPassword123!"),
                full_name="Principal System Administrator",
                role="ADMIN",
                profile_completed=True,
            )

        # Candidate user for role transition tests
        cls.target_email = "test_roles_candidate@nyayasarathi.in"
        cls.target_user = get_user_by_email(cls.target_email)
        if not cls.target_user:
            cls.target_user = create_user(
                email=cls.target_email,
                password_hash=hash_password("Candidate123!"),
                full_name="Adv. Meera Sen",
                role="USER",
                profile_completed=True,
            )

        # Deactivated Legacy Judge account
        cls.legacy_judge_email = "test_legacy_judge@nyayasarathi.in"
        cls.legacy_judge = get_user_by_email(cls.legacy_judge_email)
        if not cls.legacy_judge:
            cls.legacy_judge = create_user(
                email=cls.legacy_judge_email,
                password_hash=hash_password("JudgePassword123!"),
                full_name="Former Justice Ramesh Chandra",
                role="DEACTIVATED_JUDGE",
                profile_completed=True,
            )

        cls.user_token = create_access_token(
            user_id=cls.user["id"],
            email=cls.user["email"],
            role=cls.user["role"],
            full_name=cls.user["full_name"],
        )
        cls.advocate_token = create_access_token(
            user_id=cls.advocate["id"],
            email=cls.advocate["email"],
            role=cls.advocate["role"],
            full_name=cls.advocate["full_name"],
        )
        cls.admin_token = create_access_token(
            user_id=cls.admin["id"],
            email=cls.admin["email"],
            role=cls.admin["role"],
            full_name=cls.admin["full_name"],
        )

    # ── 1. Unauthenticated Security Boundary Tests ────────────────────────────
    def test_01_unauthenticated_requests_return_401(self):
        """Protected Admin endpoints must reject unauthenticated requests with 401."""
        endpoints = [
            ("GET", "/api/admin/dashboard"),
            ("GET", "/api/admin/users"),
            ("GET", "/api/admin/role-history"),
            ("PATCH", f"/api/admin/users/{self.target_user['id']}/role"),
        ]
        for method, url in endpoints:
            if method == "GET":
                res = self.client.get(url)
            else:
                res = self.client.patch(url, json={"new_role": "ADVOCATE", "reason": "Test"})
            self.assertEqual(
                res.status_code, 401,
                f"Endpoint {method} {url} should have returned 401 for unauthenticated request."
            )

    # ── 2. User & Advocate Cannot Access Admin Endpoints ───────────────────────
    def test_02_user_and_advocate_cannot_access_admin_endpoints(self):
        """Standard user and advocate must receive 403 Forbidden on all admin endpoints."""
        for token in [self.user_token, self.advocate_token]:
            res_dash = self.client.get(
                "/api/admin/dashboard",
                headers={"Authorization": f"Bearer {token}"}
            )
            self.assertEqual(res_dash.status_code, 403)

            res_users = self.client.get(
                "/api/admin/users",
                headers={"Authorization": f"Bearer {token}"}
            )
            self.assertEqual(res_users.status_code, 403)

            res_patch = self.client.patch(
                f"/api/admin/users/{self.target_user['id']}/role",
                headers={"Authorization": f"Bearer {token}"},
                json={"new_role": "ADMIN", "reason": "Attempted elevation"}
            )
            self.assertEqual(res_patch.status_code, 403)

    # ── 3. Complete Removal of Judge Endpoints ─────────────────────────────────
    def test_03_judge_endpoints_return_404_not_found(self):
        """All legacy judge endpoints (/api/judge/*) must return 404 Not Found."""
        judge_urls = [
            "/api/judge",
            "/api/judge/dashboard",
            "/api/judge/activity",
            "/api/judge/cases",
        ]
        for url in judge_urls:
            res = self.client.get(
                url,
                headers={"Authorization": f"Bearer {self.admin_token}"}
            )
            self.assertEqual(
                res.status_code, 404,
                f"Endpoint {url} should return 404 Not Found after Judge role removal."
            )

    # ── 4. Deprecated Judge Accounts Barred from Auth ──────────────────────────
    def test_04_judge_account_login_barred(self):
        """Accounts with JUDGE or DEACTIVATED_JUDGE role must be rejected on login with 403."""
        res = self.client.post(
            "/api/auth/login",
            json={
                "email": self.legacy_judge_email,
                "password": "JudgePassword123!",
            }
        )
        self.assertEqual(res.status_code, 403)
        self.assertIn("deactivated", res.json().get("error", "").lower())

    def test_05_legacy_judge_token_rejected_at_auth_dependency(self):
        """Tokens minted with JUDGE or DEACTIVATED_JUDGE role must be rejected with 403."""
        stale_judge_token = create_access_token(
            user_id=self.legacy_judge["id"],
            email=self.legacy_judge["email"],
            role="JUDGE",
            full_name=self.legacy_judge["full_name"],
        )
        res = self.client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {stale_judge_token}"}
        )
        self.assertEqual(res.status_code, 403)

    # ── 5. Rejection of JUDGE Role Mutation ────────────────────────────────────
    def test_06_cannot_assign_judge_role(self):
        """Attempting to set new_role='JUDGE' must return 400 Bad Request."""
        res = self.client.patch(
            f"/api/admin/users/{self.target_user['id']}/role",
            headers={"Authorization": f"Bearer {self.admin_token}"},
            json={
                "new_role": "JUDGE",
                "reason": "Attempting invalid judge assignment",
            }
        )
        self.assertEqual(res.status_code, 400)
        self.assertIn("invalid target role", res.json().get("error", "").lower())

    # ── 6. Admin Functionality & ADVOCATE Role Transition ──────────────────────
    def test_07_admin_can_view_metrics_and_users(self):
        """An administrator can read system metrics and list users with pagination."""
        res_dash = self.client.get(
            "/api/admin/dashboard",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        self.assertEqual(res_dash.status_code, 200)
        data = res_dash.json()
        self.assertGreaterEqual(data["total_users"], 1)
        self.assertIn("role_counts", data)
        self.assertIn("ADVOCATE", data["role_counts"])

        res_users = self.client.get(
            "/api/admin/users?limit=10&offset=0",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        self.assertEqual(res_users.status_code, 200)
        users_data = res_users.json()
        self.assertIn("items", users_data)
        self.assertGreaterEqual(users_data["total"], 1)

    def test_08_admin_role_change_to_advocate_and_audit_persistence(self):
        """Admin promoting USER to ADVOCATE must persist in DB and write an audit record."""
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
                "new_role": "ADVOCATE",
                "reason": "Verified Bar Council Enrollment No. D/1042/2020",
            }
        )
        self.assertEqual(res.status_code, 200)
        resp_data = res.json()
        self.assertTrue(resp_data["success"])
        self.assertEqual(resp_data["old_role"], "USER")
        self.assertEqual(resp_data["new_role"], "ADVOCATE")

        # Verify persistence in database
        updated_db_user = get_user_by_id(self.target_user["id"])
        self.assertEqual(updated_db_user["role"], "ADVOCATE")

        # Verify audit history
        res_audit = self.client.get(
            f"/api/admin/role-history?target_user_id={self.target_user['id']}",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        self.assertEqual(res_audit.status_code, 200)
        audits = res_audit.json()["items"]
        self.assertGreaterEqual(len(audits), 1)
        latest = audits[0]
        self.assertEqual(latest["new_role"], "ADVOCATE")
        self.assertEqual(latest["reason"], "Verified Bar Council Enrollment No. D/1042/2020")

    # ── 7. Safety Guards: Self-Demotion, Invalid Targets ───────────────────────
    def test_09_admin_cannot_demote_self(self):
        """Prevent self-demotion to avoid administrator lockout."""
        res = self.client.patch(
            f"/api/admin/users/{self.admin['id']}/role",
            headers={"Authorization": f"Bearer {self.admin_token}"},
            json={"new_role": "USER", "reason": "Accidental self-demotion"}
        )
        self.assertEqual(res.status_code, 400)
        self.assertIn("demote themselves", res.json().get("error", ""))

    def test_10_invalid_user_returns_404(self):
        """Attempting to mutate a nonexistent user ID must return 404."""
        res = self.client.patch(
            "/api/admin/users/non-existent-user-id-99999/role",
            headers={"Authorization": f"Bearer {self.admin_token}"},
            json={"new_role": "ADVOCATE", "reason": "Test"}
        )
        self.assertEqual(res.status_code, 404)

    def test_11_invalid_role_returns_400(self):
        """Attempting to set an unsupported role must return 400."""
        res = self.client.patch(
            f"/api/admin/users/{self.target_user['id']}/role",
            headers={"Authorization": f"Bearer {self.admin_token}"},
            json={"new_role": "SUPER_OVERLORD", "reason": "Invalid"}
        )
        self.assertEqual(res.status_code, 400)

    # ── 8. Public Signup Role Tampering Prevention ─────────────────────────────
    def test_12_signup_prevents_client_elevated_role_injection(self):
        """Public signup must ignore attempts to self-assign ADMIN or ADVOCATE."""
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
        self.assertEqual(data["user"]["role"], "USER")
        self.assertNotEqual(data["user"]["role"], "ADMIN")


if __name__ == "__main__":
    unittest.main()
