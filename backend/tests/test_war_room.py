"""
Unit & Integration Tests for NyayaSarathi Legal War Room
Tests session CRUD, analysis operations, caching, usage logging, and report export.
"""

import os
import sys
import pytest
from fastapi.testclient import TestClient

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from main import app
from services.war_room_repository import init_war_room_tables

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    init_war_room_tables()


def test_war_room_lifecycle_and_analysis():
    # 1. Create a War Room session
    create_payload = {
        "title": "State of Maharashtra v. Rajesh Sharma",
        "description": "Applicant seeks anticipatory bail under Section 438 CrPC in FIR No. 102/2024 for alleged offences under Section 420, 406 IPC. Clean antecedents, dispute is civil breach of contract.",
        "case_type": "bail",
        "jurisdiction": "High Court",
        "court": "Bombay High Court",
        "user_position": "applicant",
        "opposing_party": "State of Maharashtra & Complainant",
        "relevant_dates": [
            {"event_date": "2024-02-10", "description": "FIR registered at Bandra Police Station", "source_reference": "FIR No. 102/2024"},
            {"event_date": "2024-03-01", "description": "Notice issued under Section 41A CrPC", "source_reference": "Police Notice"},
        ],
        "selected_doc_ids": [],
    }

    res = client.post("/api/war-room", json=create_payload)
    assert res.status_code == 201
    data = res.json()
    session_id = data["id"]
    assert data["title"] == create_payload["title"]
    assert data["user_position"] == "applicant"

    # 2. List sessions
    list_res = client.get("/api/war-room")
    assert list_res.status_code == 200
    sessions = list_res.json()
    assert any(s["id"] == session_id for s in sessions)

    # 3. Get single session
    get_res = client.get(f"/api/war-room/{session_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == session_id

    # 4. Update session
    update_res = client.patch(f"/api/war-room/{session_id}", json={"court": "Bombay High Court (Principal Seat)"})
    assert update_res.status_code == 200
    assert update_res.json()["court"] == "Bombay High Court (Principal Seat)"

    # 5. Execute Facts Analysis
    facts_res = client.post(f"/api/war-room/{session_id}/analyze", json={"operation": "facts"})
    assert facts_res.status_code == 200
    facts_data = facts_res.json()
    assert facts_data["operation"] == "facts"
    assert isinstance(facts_data["result"], list)
    assert len(facts_data["result"]) > 0

    # Test cache hit on second run
    facts_cached_res = client.post(f"/api/war-room/{session_id}/analyze", json={"operation": "facts"})
    assert facts_cached_res.status_code == 200
    assert facts_cached_res.json()["cache_hit"] is True

    # 6. Execute Evidence Analysis
    ev_res = client.post(f"/api/war-room/{session_id}/analyze", json={"operation": "evidence"})
    assert ev_res.status_code == 200
    assert isinstance(ev_res.json()["result"], list)

    # 7. Execute Arguments Building
    arg_res = client.post(f"/api/war-room/{session_id}/analyze", json={"operation": "arguments"})
    assert arg_res.status_code == 200
    assert isinstance(arg_res.json()["result"], list)
    assert len(arg_res.json()["result"]) > 0
    first_arg = arg_res.json()["result"][0]
    assert "main_claim" in first_arg
    assert "applicable_provisions" in first_arg

    # 8. Execute Opposition Simulation (Devil's Advocate)
    opp_res = client.post(f"/api/war-room/{session_id}/analyze", json={"operation": "opposition"})
    assert opp_res.status_code == 200
    assert isinstance(opp_res.json()["result"], list)
    first_opp = opp_res.json()["result"][0]
    assert "opposing_claim" in first_opp
    assert "suggested_rebuttal_counterarguments" in first_opp

    # 9. Execute Precedent Research from local database
    prec_res = client.post(f"/api/war-room/{session_id}/analyze", json={"operation": "precedents"})
    assert prec_res.status_code == 200
    assert isinstance(prec_res.json()["result"], list)
    assert len(prec_res.json()["result"]) > 0
    first_prec = prec_res.json()["result"][0]
    assert "cnr" in first_prec
    assert "verbatim_excerpt" in first_prec

    # 10. Execute Risks Assessment
    risk_res = client.post(f"/api/war-room/{session_id}/analyze", json={"operation": "risks"})
    assert risk_res.status_code == 200
    assert isinstance(risk_res.json()["result"], list)

    # 11. Generate Strategy Report
    rep_res = client.post(f"/api/war-room/{session_id}/analyze", json={"operation": "report"})
    assert rep_res.status_code == 200
    report_data = rep_res.json()["result"]
    assert "executive_summary" in report_data
    assert "disclaimer" in report_data

    # 12. Export Strategy Report
    export_res = client.post(f"/api/war-room/{session_id}/export")
    assert export_res.status_code == 200
    assert "NyayaSarathi Legal Strategy Report" in export_res.text

    # 13. Check Usage Summary
    usage_res = client.get(f"/api/war-room/{session_id}/usage")
    assert usage_res.status_code == 200
    usage_data = usage_res.json()
    assert usage_data["total_requests"] >= 6
    assert usage_data["total_cache_hits"] >= 1

    # 14. Delete Session
    del_res = client.delete(f"/api/war-room/{session_id}")
    assert del_res.status_code == 204

    # Verify session deleted
    assert client.get(f"/api/war-room/{session_id}").status_code == 404
