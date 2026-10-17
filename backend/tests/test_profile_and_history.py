"""
Unit and Integration Tests for Profile and User History.
Tests:
  - Reading member profile via GET /api/profile/me
  - Updating allowed profile fields via PATCH /api/profile/me
  - Forbidding role/id mutation through profile endpoint
  - Profile completion onboarding via POST /api/profile/complete
  - Storing and retrieving isolated user activity history
  - User activity pagination and delete ownership enforcement
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
from services.user_repository import create_user, get_user_by_email, get_user_activities


class TestProfileAndHistory(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        
        # Test User 1 (Advocate)
        cls.email_1 = "test_profile_user1@nyayasarathi.in"
        cls.user_1 = get_user_by_email(cls.email_1)
        if not cls.user_1:
            cls.user_1 = create_user(
                email=cls.email_1,
                password_hash=None,
                full_name="Adv. Priya Sharma",
                role="USER",
                profile_completed=False,
            )

        # Test User 2 (Separate user for isolation tests)
        cls.email_2 = "test_profile_user2@nyayasarathi.in"
        cls.user_2 = get_user_by_email(cls.email_2)
        if not cls.user_2:
            cls.user_2 = create_user(
                email=cls.email_2,
                password_hash=None,
                full_name="Adv. Vikram Malhotra",
                role="USER",
                profile_completed=True,
            )

        cls.token_1 = create_access_token(
            user_id=cls.user_1["id"],
            email=cls.user_1["email"],
            role=cls.user_1["role"],
            full_name=cls.user_1["full_name"],
        )
        cls.token_2 = create_access_token(
            user_id=cls.user_2["id"],
            email=cls.user_2["email"],
            role=cls.user_2["role"],
            full_name=cls.user_2["full_name"],
        )

    def test_01_get_my_profile(self):
        """Verify GET /api/profile/me returns authenticated user's profile."""
        res = self.client.get(
            "/api/profile/me",
            headers={"Authorization": f"Bearer {self.token_1}"},
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["email"], self.email_1)
        self.assertEqual(data["id"], self.user_1["id"])
        self.assertEqual(data["role"], "USER")

    def test_02_update_permitted_profile_fields(self):
        """Verify PATCH /api/profile/me allows updating organization & designation."""
        res = self.client.patch(
            "/api/profile/me",
            headers={"Authorization": f"Bearer {self.token_1}"},
            json={
                "organization": "Delhi High Court Chambers",
                "designation": "Senior Advocate",
                "avatar_url": "https://example.com/avatar.jpg",
            },
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["organization"], "Delhi High Court Chambers")
        self.assertEqual(data["designation"], "Senior Advocate")
        self.assertEqual(data["avatar_url"], "https://example.com/avatar.jpg")

    def test_03_role_tampering_is_prevented(self):
        """Verify user cannot escalate their role to ADMIN or JUDGE through profile update."""
        # Attempt to pass role in payload
        res = self.client.patch(
            "/api/profile/me",
            headers={"Authorization": f"Bearer {self.token_1}"},
            json={
                "role": "ADMIN",
                "organization": "Supreme Court of India",
            },
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        # Role must remain USER
        self.assertEqual(data["role"], "USER")

    def test_04_profile_completion_onboarding(self):
        """Verify POST /api/profile/complete sets profile_completed to True."""
        res = self.client.post(
            "/api/profile/complete",
            headers={"Authorization": f"Bearer {self.token_1}"},
            json={
                "full_name": "Adv. Priya Sharma",
                "organization": "Bombay High Court Bar",
                "designation": "Advocate on Record",
            },
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["profile_completed"])
        self.assertEqual(data["designation"], "Advocate on Record")

    def test_05_record_and_retrieve_activity_history(self):
        """Verify user can record activity and retrieve their own history."""
        # Record an activity for User 1
        create_res = self.client.post(
            "/api/history",
            headers={"Authorization": f"Bearer {self.token_1}"},
            json={
                "activity_type": "LEGAL_RESEARCH",
                "title": "Bail jurisprudence research under BNSS 482",
                "query_text": "Anticipatory bail considerations in economic offenses",
                "metadata": {"doc_count": 2},
            },
        )
        self.assertEqual(create_res.status_code, 201)
        created_item = create_res.json()
        activity_id = created_item["id"]

        # Fetch history for User 1
        list_res = self.client.get(
            "/api/history",
            headers={"Authorization": f"Bearer {self.token_1}"},
        )
        self.assertEqual(list_res.status_code, 200)
        items = list_res.json()["items"]
        item_ids = [it["id"] for it in items]
        self.assertIn(activity_id, item_ids)

    def test_06_activity_history_isolation_between_users(self):
        """Verify User 2 CANNOT view or delete User 1's private history records."""
        # Create item for User 1
        create_res = self.client.post(
            "/api/history",
            headers={"Authorization": f"Bearer {self.token_1}"},
            json={
                "activity_type": "DOCUMENT_UPLOAD",
                "title": "Private Client Brief.pdf",
            },
        )
        user1_item_id = create_res.json()["id"]

        # User 2 lists their own history — user1_item_id must NOT appear
        user2_list = self.client.get(
            "/api/history",
            headers={"Authorization": f"Bearer {self.token_2}"},
        )
        self.assertEqual(user2_list.status_code, 200)
        user2_item_ids = [it["id"] for it in user2_list.json()["items"]]
        self.assertNotIn(user1_item_id, user2_item_ids)

        # User 2 tries to delete User 1's history record — must fail with 404
        delete_res = self.client.delete(
            f"/api/history/{user1_item_id}",
            headers={"Authorization": f"Bearer {self.token_2}"},
        )
        self.assertEqual(delete_res.status_code, 404)

        # User 1 deletes their own record — succeeds with 204
        own_delete_res = self.client.delete(
            f"/api/history/{user1_item_id}",
            headers={"Authorization": f"Bearer {self.token_1}"},
        )
        self.assertEqual(own_delete_res.status_code, 204)


if __name__ == "__main__":
    unittest.main()
