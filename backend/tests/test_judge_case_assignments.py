"""
NyayaSarathi Regression Tests:
Judge Access Control, Persistent Case Assignments, and Precedent Explorer Decoupling.
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
    create_user,
    delete_user_by_id,
    create_case_assignment,
    delete_case_assignment,
    create_activity,
    init_user_table,
)
from services.auth_service import create_access_token


class TestJudgeCaseAssignmentsAndAccessControl(unittest.TestCase):
    def setUp(self):
        init_user_table()
        self.client = TestClient(app)
        self.suffix = uuid.uuid4().hex[:8]

        # 1. Admin account
        self.admin = create_user(
            email=f"admin_case_{self.suffix}@nyayasarathi.in",
            password_hash="testhash123",
            full_name=f"Admin Case {self.suffix}",
            role="ADMIN",
        )
        self.admin_token = create_access_token(
            user_id=self.admin["id"],
            email=self.admin["email"],
            role="ADMIN",
            full_name=self.admin["full_name"],
        )

        # 2. Judge A
        self.judge_a = create_user(
            email=f"judge_a_{self.suffix}@nyayasarathi.in",
            password_hash="testhash123",
            full_name=f"Hon'ble Justice A {self.suffix}",
            role="JUDGE",
        )
        self.judge_a_token = create_access_token(
            user_id=self.judge_a["id"],
            email=self.judge_a["email"],
            role="JUDGE",
            full_name=self.judge_a["full_name"],
        )

        # 3. Judge B
        self.judge_b = create_user(
            email=f"judge_b_{self.suffix}@nyayasarathi.in",
            password_hash="testhash123",
            full_name=f"Hon'ble Justice B {self.suffix}",
            role="JUDGE",
        )
        self.judge_b_token = create_access_token(
            user_id=self.judge_b["id"],
            email=self.judge_b["email"],
            role="JUDGE",
            full_name=self.judge_b["full_name"],
        )

        # 4. Standard User / Citizen
        self.citizen = create_user(
            email=f"citizen_{self.suffix}@nyayasarathi.in",
            password_hash="testhash123",
            full_name=f"Citizen User {self.suffix}",
            role="USER",
        )
        self.citizen_token = create_access_token(
            user_id=self.citizen["id"],
            email=self.citizen["email"],
            role="USER",
            full_name=self.citizen["full_name"],
        )

        self.created_assignments = []

    def tearDown(self):
        for cid in self.created_assignments:
            try:
                delete_case_assignment(cid)
            except Exception:
                pass
        delete_user_by_id(self.citizen["id"])
        delete_user_by_id(self.judge_b["id"])
        delete_user_by_id(self.judge_a["id"])
        delete_user_by_id(self.admin["id"])

    def test_01_privacy_isolation_judge_cannot_view_citizen_activity(self):
        """CRITICAL: Judge requesting /api/judge/activity must NEVER see private citizen activity."""
        # Citizen creates private activity
        create_activity(
            user_id=self.citizen["id"],
            activity_type="LEGAL_RESEARCH",
            title="Private Citizen Bail Application Research",
        )

        # Judge A queries activity feed
        res = self.client.get(
            "/api/judge/activity",
            headers={"Authorization": f"Bearer {self.judge_a_token}"},
        )
        self.assertEqual(res.status_code, 200)
        items = res.json()["items"]
        titles = [i["title"] for i in items]
        self.assertNotIn(
            "Private Citizen Bail Application Research",
            titles,
            "Privacy breach: Judge accessed confidential citizen activity!"
        )

    def test_02_admin_can_assign_case_to_judge(self):
        """Admin assigns a litigation matter to verified judge."""
        payload = {
            "case_number": f"CRL.A. {self.suffix}/2026",
            "title": "State of Maharashtra vs. Accused A",
            "court_name": "High Court of Judicature at Bombay",
            "judge_id": self.judge_a["id"],
            "case_type": "Criminal Appeal",
            "priority": "URGENT",
            "petitioner": "State of Maharashtra",
            "respondent": "Accused A",
            "notes": "Listed for urgent bail hearing",
        }
        res = self.client.post(
            "/api/admin/cases/assign",
            json=payload,
            headers={"Authorization": f"Bearer {self.admin_token}"},
        )
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertEqual(data["case_number"], payload["case_number"])
        self.assertEqual(data["judge_id"], self.judge_a["id"])
        self.assertEqual(data["status"], "ASSIGNED")
        self.created_assignments.append(data["id"])

    def test_03_reject_case_assignment_to_non_judge(self):
        """Admin attempting to assign a case to a regular USER must be rejected."""
        payload = {
            "case_number": f"CIV.P. {self.suffix}/2026",
            "title": "Invalid Case Assignment Test",
            "court_name": "District Court",
            "judge_id": self.citizen["id"],  # Citizen is USER, not JUDGE!
        }
        res = self.client.post(
            "/api/admin/cases/assign",
            json=payload,
            headers={"Authorization": f"Bearer {self.admin_token}"},
        )
        self.assertEqual(res.status_code, 400)
        error_msg = res.json().get("error") or res.json().get("detail", "")
        self.assertIn("JUDGE", error_msg)

    def test_04_unauthorized_user_cannot_assign_case(self):
        """Standard citizen or judge cannot assign cases (Admin operation only)."""
        payload = {
            "case_number": f"CRL.A. {self.suffix}/2026",
            "title": "Unauthorized Assignment Test",
            "court_name": "High Court",
            "judge_id": self.judge_a["id"],
        }
        # Citizen attempt
        res_cit = self.client.post(
            "/api/admin/cases/assign",
            json=payload,
            headers={"Authorization": f"Bearer {self.citizen_token}"},
        )
        self.assertEqual(res_cit.status_code, 403)

        # Judge attempt
        res_judge = self.client.post(
            "/api/admin/cases/assign",
            json=payload,
            headers={"Authorization": f"Bearer {self.judge_a_token}"},
        )
        self.assertEqual(res_judge.status_code, 403)

    def test_05_docket_scoping_judge_only_sees_assigned_matters(self):
        """Judge A only sees cases assigned to Judge A; Judge B does not see Judge A's cases."""
        # Create assignment for Judge A
        c1 = create_case_assignment(
            case_number=f"CRL.M. {self.suffix}-1/2026",
            title="Matter for Judge A",
            court_name="High Court Bench 1",
            judge_id=self.judge_a["id"],
        )
        self.created_assignments.append(c1["id"])

        # Judge A queries cases
        res_a = self.client.get(
            "/api/judge/cases",
            headers={"Authorization": f"Bearer {self.judge_a_token}"},
        )
        self.assertEqual(res_a.status_code, 200)
        case_nums_a = [i["case_number"] for i in res_a.json()["items"]]
        self.assertIn(c1["case_number"], case_nums_a)

        # Judge B queries cases
        res_b = self.client.get(
            "/api/judge/cases",
            headers={"Authorization": f"Bearer {self.judge_b_token}"},
        )
        self.assertEqual(res_b.status_code, 200)
        case_nums_b = [i["case_number"] for i in res_b.json()["items"]]
        self.assertNotIn(c1["case_number"], case_nums_b)

    def test_06_judge_cannot_modify_other_judges_case(self):
        """Judge B cannot update docket status on a case assigned to Judge A."""
        c = create_case_assignment(
            case_number=f"CRL.M. {self.suffix}-2/2026",
            title="Matter Owned by Judge A",
            court_name="High Court Bench 1",
            judge_id=self.judge_a["id"],
        )
        self.created_assignments.append(c["id"])

        # Judge B attempts to update
        res = self.client.patch(
            f"/api/judge/cases/{c['id']}",
            json={"status": "DISPOSED", "notes": "Unauthorized disposal attempt"},
            headers={"Authorization": f"Bearer {self.judge_b_token}"},
        )
        self.assertEqual(res.status_code, 403)

        # Judge A updates legitimately
        res_a = self.client.patch(
            f"/api/judge/cases/{c['id']}",
            json={"status": "IN_REVIEW", "notes": "Chamber review underway"},
            headers={"Authorization": f"Bearer {self.judge_a_token}"},
        )
        self.assertEqual(res_a.status_code, 200)
        self.assertEqual(res_a.json()["status"], "IN_REVIEW")

    def test_07_precedent_endpoint_is_decoupled_from_docket(self):
        """Verifies GET /api/judge/precedents returns legal precedents catalog clearly labeled."""
        res = self.client.get(
            "/api/judge/precedents",
            headers={"Authorization": f"Bearer {self.judge_a_token}"},
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("Public Legal Precedents", data["notice"])
        self.assertIsInstance(data["items"], list)


if __name__ == "__main__":
    unittest.main()
