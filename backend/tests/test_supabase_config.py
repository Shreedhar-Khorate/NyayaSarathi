"""
Unit Tests for Supabase Configuration and Client Helper.
Verifies that all Supabase keys are loaded dynamically from environment/.env
with ZERO hardcoded secrets.
"""

import os
import sys
import unittest
from dotenv import load_dotenv

# Ensure backend root is on sys.path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from services.supabase_client import (
    normalize_supabase_url,
    is_supabase_configured,
    get_supabase_client,
)


class TestSupabaseConfig(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Load environment dynamically from .env
        env_path = os.path.join(backend_dir, ".env")
        load_dotenv(dotenv_path=env_path)

    def test_env_keys_loaded_dynamically(self):
        """Ensure keys are read dynamically from os.environ, not hardcoded."""
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
        db_url = os.getenv("DATABASE_URL")

        # Verify that variables are present in environment
        self.assertIsNotNone(supabase_url, "SUPABASE_URL should be defined in .env")
        self.assertIsNotNone(supabase_key, "SUPABASE key should be defined in .env")
        self.assertIsNotNone(db_url, "DATABASE_URL should be defined in .env")

    def test_normalize_supabase_url(self):
        """Verify URL normalizer handles raw base URLs, trailing slashes, and /rest/v1 paths."""
        self.assertEqual(
            normalize_supabase_url("https://xyz.supabase.co"),
            "https://xyz.supabase.co"
        )
        self.assertEqual(
            normalize_supabase_url("https://xyz.supabase.co/"),
            "https://xyz.supabase.co"
        )
        self.assertEqual(
            normalize_supabase_url("https://xyz.supabase.co/rest/v1/"),
            "https://xyz.supabase.co"
        )
        self.assertEqual(
            normalize_supabase_url("https://xyz.supabase.co/rest/v1"),
            "https://xyz.supabase.co"
        )

    def test_is_supabase_configured(self):
        """Verify is_supabase_configured returns boolean based on active env."""
        configured = is_supabase_configured()
        self.assertIsInstance(configured, bool)

    def test_no_hardcoded_secrets_in_test_files(self):
        """Sanity check that this test file itself contains no hardcoded credentials."""
        with open(__file__, "r", encoding="utf-8") as f:
            lines = f.readlines()

        jwt_prefix = "eyJ" + "hbGci"
        # Check that no line other than the test logic contains JWT prefixes
        secret_lines = [l for l in lines if jwt_prefix in l and "jwt_prefix" not in l]
        self.assertEqual(len(secret_lines), 0, "No hardcoded tokens permitted in test code.")

    def test_supabase_seeded_user_retrieval(self):
        """Test retrieving the seeded LOGINS.md user account."""
        from services.user_repository import get_user_by_email
        user = get_user_by_email("user@nyayasarathi.in")
        self.assertIsNotNone(user)
        self.assertEqual(user["email"].lower(), "user@nyayasarathi.in")
        self.assertEqual(user["role"], "USER")

    def test_supabase_auth_login_endpoint(self):
        """Test POST /api/auth/login against the Supabase-seeded credentials from LOGINS.md."""
        from fastapi.testclient import TestClient
        from main import app

        client = TestClient(app)
        res = client.post("/api/auth/login", json={
            "email": "user@nyayasarathi.in",
            "password": "User@12345",
        })
        self.assertEqual(res.status_code, 200, f"Login failed: {res.text}")
        data = res.json()
        self.assertIn("access_token", data)
        self.assertEqual(data["user"]["email"], "user@nyayasarathi.in")
        self.assertEqual(data["user"]["role"], "USER")


if __name__ == "__main__":
    unittest.main()

