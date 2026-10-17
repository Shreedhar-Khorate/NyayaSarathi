"""
NyayaSarathi Regression Tests:
Secure Initial Administrator Bootstrap & Public Signup Role Restrictions.
"""

import os
import sys
import unittest
import uuid
from fastapi.testclient import TestClient

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from main import app
from services.user_repository import (
    get_user_by_email,
    delete_user_by_id,
    init_user_table,
)
from services.auth_service import verify_password
from scripts.bootstrap_admin import bootstrap_admin, validate_password_strength


class TestBootstrapAdminAndSignupSecurity(unittest.TestCase):
    def setUp(self):
        init_user_table()
        self.client = TestClient(app)
        self.suffix = uuid.uuid4().hex[:8]
        self.test_email = f"boot_admin_{self.suffix}@nyayasarathi.in"

    def tearDown(self):
        u = get_user_by_email(self.test_email)
        if u:
            delete_user_by_id(u["id"])

    def test_01_public_signup_cannot_create_administrator(self):
        """CRITICAL: Public signup must unconditionally assign USER role even if caller passes ADMIN."""
        payload = {
            "email": self.test_email,
            "password": "StrongPassword@123",
            "full_name": "Infiltrator Account",
            "role": "ADMIN",  # Attacker attempts privilege escalation
        }
        res = self.client.post("/api/auth/signup", json=payload)
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertEqual(data["user"]["role"], "USER")

        # Double check authoritative database record
        db_user = get_user_by_email(self.test_email)
        self.assertIsNotNone(db_user)
        self.assertEqual(db_user["role"], "USER")

    def test_02_bootstrap_creates_admin_with_bcrypt_hash(self):
        """Verify bootstrap_admin CLI creates admin with secure bcrypt hash."""
        code = bootstrap_admin(
            email=self.test_email,
            password="SecurePass987!",
            name=f"Bootstrap Admin {self.suffix}",
        )
        self.assertEqual(code, 0)

        db_user = get_user_by_email(self.test_email)
        self.assertIsNotNone(db_user)
        self.assertEqual(db_user["role"], "ADMIN")
        # Ensure password is not plaintext
        self.assertNotEqual(db_user["password_hash"], "SecurePass987!")
        self.assertTrue(db_user["password_hash"].startswith("$2b$"))
        # Verify hash matches
        self.assertTrue(verify_password("SecurePass987!", db_user["password_hash"]))

    def test_03_bootstrap_cannot_overwrite_admin_without_flag(self):
        """Verify re-running bootstrap against existing admin does NOT overwrite password without --reset-password."""
        # 1. Create admin
        bootstrap_admin(
            email=self.test_email,
            password="OriginalPassword1",
            name="Original Admin",
        )
        user_before = get_user_by_email(self.test_email)
        orig_hash = user_before["password_hash"]

        # 2. Re-run without reset_password flag
        code = bootstrap_admin(
            email=self.test_email,
            password="AttackerPassword2",
            name="Malicious Overwrite",
            reset_password=False,
        )
        self.assertEqual(code, 0)

        # 3. Verify hash did not change
        user_after = get_user_by_email(self.test_email)
        self.assertEqual(user_after["password_hash"], orig_hash)
        self.assertTrue(verify_password("OriginalPassword1", user_after["password_hash"]))
        self.assertFalse(verify_password("AttackerPassword2", user_after["password_hash"]))

    def test_04_bootstrap_with_reset_flag_safely_rotates_password(self):
        """Verify explicit --reset-password rotates admin credentials cleanly."""
        bootstrap_admin(
            email=self.test_email,
            password="OriginalPassword1",
            name="Original Admin",
        )
        # Rotate password
        code = bootstrap_admin(
            email=self.test_email,
            password="RotatedPassword2",
            reset_password=True,
        )
        self.assertEqual(code, 0)

        user_after = get_user_by_email(self.test_email)
        self.assertTrue(verify_password("RotatedPassword2", user_after["password_hash"]))
        self.assertFalse(verify_password("OriginalPassword1", user_after["password_hash"]))

    def test_05_bootstrap_rejects_weak_passwords(self):
        """Verify weak passwords fail validation and do not create accounts."""
        self.assertFalse(validate_password_strength("short1"))
        self.assertFalse(validate_password_strength("alllettersonly"))
        self.assertFalse(validate_password_strength("1234567890"))
        self.assertTrue(validate_password_strength("ValidPassword123"))

        code = bootstrap_admin(
            email=self.test_email,
            password="weak",
            name="Weak Password Test",
        )
        self.assertEqual(code, 1)
        self.assertIsNone(get_user_by_email(self.test_email))


if __name__ == "__main__":
    unittest.main()
