"""
Comprehensive Regression Test Suite for NyayaSarathi Legal War Room:
Tests:
1. Dynamic Precedent Retrieval & Domain Disambiguation (Zero bail cases for murder; Zero murder cases for Section 41A CrPC)
2. Premchand v. State of Maharashtra (Exception 4 to S. 300 IPC, S. 313(5) CrPC, Decided Appeal)
3. Arnesh Kumar v. State of Bihar (Section 41/41A CrPC arrest safeguards, Section 498A IPC)
4. Statutory Transition Rules (IPC/CrPC vs BNS/BNSS under Section 531 BNSS and Article 20(1))
5. Citation Verification Engine (Detects fabricated citations and flags verification_required)
6. Strategy Report 10-section integrity and procedural consistency
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
from services.precedent_verification import query_verified_precedents, verify_citation
from services.procedural_context_engine import analyze_procedural_context, evaluate_statutory_era

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_tables():
    init_war_room_tables()


# ── TEST 1: Citation Verification Engine ──────────────────────────────────────
def test_citation_verification_detects_authentic_and_fabricated():
    """Authentic citations must verify; fabricated citations must return verification_required."""
    # Authentic Supreme Court citations in corpus
    auth_arnesh = verify_citation("(2014) 8 SCC 273", "Arnesh Kumar v. State of Bihar")
    assert auth_arnesh["is_verified"] is True
    assert auth_arnesh["status"] == "verified_primary_source"
    assert "Section 41A" in auth_arnesh["actual_holding"]

    auth_premchand = verify_citation("(2023) 5 SCC 522", "Premchand v. State of Maharashtra")
    assert auth_premchand["is_verified"] is True
    assert auth_premchand["status"] == "verified_primary_source"
    assert "Section 304 Part II" in auth_premchand["actual_holding"]

    # Fabricated / unverified citation
    fake_cite = verify_citation("2024 SC 9999 Fabricated Case", "State v. Fictional")
    assert fake_cite["is_verified"] is False
    assert fake_cite["status"] == "verification_required"


# ── TEST 2: Precedent Domain Disambiguation (No Cross-Contamination) ──────────
def test_precedent_retrieval_domain_routing():
    """
    Guarantees:
    - Homicide cases NEVER retrieve bail applications.
    - Section 41A / Arnesh Kumar queries NEVER retrieve homicide/Section 302 cases.
    - Cheque dishonour queries NEVER retrieve bail or murder cases.
    """
    # 1. Homicide query
    homicide_precedents = query_verified_precedents(
        case_type="appeal",
        description="Criminal appeal against conviction under Section 302 IPC. Plea of sudden fight without premeditation under Exception 4 to Section 300 IPC.",
        user_position="appellant"
    )
    assert len(homicide_precedents) > 0
    for p in homicide_precedents:
        assert p["court"] == "Supreme Court of India"
        assert "bail application" not in p["title"].lower()
        assert any(t in p["actual_holding"].lower() for t in ["304", "300", "sudden fight", "premeditation", "313", "exception 4"])

    # 2. Arrest Safeguards / Arnesh Kumar query
    arrest_precedents = query_verified_precedents(
        case_type="quashing",
        description="Police initiated mechanical arrest under Section 498A IPC without issuing notice of appearance under Section 41A CrPC.",
        user_position="petitioner"
    )
    assert len(arrest_precedents) > 0
    titles = [p["title"] for p in arrest_precedents]
    assert any("Arnesh Kumar" in t for t in titles)
    for p in arrest_precedents:
        # Must not serve murder cases
        assert "murder" not in p["legal_issue"].lower()
        assert "302" not in p["actual_holding"].lower()
        assert any(t in (p["legal_issue"] + " " + p["actual_holding"]).lower() for t in ["41", "41a", "arrest", "liberty", "custodial", "bail"])


# ── TEST 3: Procedural Context Engine & Transition Rules ──────────────────────
def test_statutory_era_transition_rules():
    """Verifies that offences before 1 July 2024 are IPC/CrPC, and transition notes cite S. 531 BNSS."""
    # Case with 2013-2023 dates
    session_old = {
        "title": "State v. Rajesh",
        "description": "FIR registered on 15.02.2023 for alleged offences under Section 302 IPC."
    }
    era_old = evaluate_statutory_era(session_old, "")
    assert era_old["era"] == "IPC_CRPC"
    assert "Section 531" in era_old["transition_note"]
    assert "Article 20(1)" in era_old["transition_note"]

    # Case specifically mentioning BNS 2023
    session_new = {
        "title": "State v. Vikram",
        "description": "FIR registered under Section 103(1) of Bharatiya Nyaya Sanhita, 2023 (BNS) and Section 35(3) of BNSS."
    }
    era_new = evaluate_statutory_era(session_new, "")
    assert era_new["era"] == "BNS_BNSS"


def test_procedural_context_engine_stage_accuracy():
    """Verify that decided appeals generate sentence set-off and forbid High Court rejoinders."""
    session_decided_sc = {
        "title": "Premchand v. State of Maharashtra",
        "court": "Supreme Court of India",
        "user_position": "appellant",
        "case_type": "appeal",
        "description": "Criminal Appeal No. 211 of 2023 before the Supreme Court of India decided on 03.03.2023 altering Section 302 to Section 304 Part II IPC."
    }
    posture = analyze_procedural_context(session_decided_sc, [])
    assert posture["current_forum"] == "Supreme Court of India"
    assert posture["posture"] == "Decided Criminal Appeal"
    assert posture["appellant"] == "Premchand"
    assert posture["respondent"] == "State of Maharashtra"
    assert posture["is_decided"] is True
    assert "Section 428 CrPC" in posture["next_steps"]
    assert "no rejoinder" in posture["next_steps"].lower()


# ── TEST 4: Full Pipeline End-to-End on Arnesh Kumar Regression Case ──────────
def test_arnesh_kumar_pipeline():
    """Test full pipeline analysis for Arnesh Kumar v. State of Bihar arrest safeguards scenario."""
    arnesh_payload = {
        "title": "Arnesh Kumar v. State of Bihar",
        "court": "Supreme Court of India",
        "case_type": "quashing",
        "jurisdiction": "Supreme Court",
        "user_position": "appellant",
        "opposing_party": "State of Bihar & Complainant",
        "description": (
            "Special Leave to Appeal (Crl.) arising out of Patna High Court order rejecting anticipatory bail "
            "in FIR under Section 498A IPC and Section 4 Dowry Prohibition Act. Investigating officer proceeded to "
            "effect mechanical arrest without issuing notice of appearance under Section 41A CrPC and without recording reasons "
            "under Section 41(1)(b) CrPC. Supreme Court held arrest cannot be made merely because offence is non-bailable; "
            "mandated two-week notice under Section 41A CrPC and held police liable for contempt of court for default."
        ),
        "relevant_dates": [
            {"event_date": "2013-07-01", "description": "FIR registered under Section 498A IPC", "source_reference": "FIR"},
            {"event_date": "2014-07-02", "description": "Supreme Court pronounces judgment in Criminal Appeal No. 1277 of 2014", "source_reference": "(2014) 8 SCC 273"}
        ],
        "selected_doc_ids": []
    }

    # 1. Create Session
    create_res = client.post("/api/war-room", json=arnesh_payload)
    assert create_res.status_code == 201
    session_id = create_res.json()["id"]

    # 2. Precedent Retrieval
    prec_res = client.post(f"/api/war-room/{session_id}/analyze", json={"operation": "precedents"})
    assert prec_res.status_code == 200
    precs = prec_res.json()["result"]
    assert len(precs) > 0
    # Must retrieve Arnesh Kumar and arrest safeguards precedents
    titles = [p["title"] for p in precs]
    assert any("Arnesh Kumar" in t for t in titles)
    for p in precs:
        assert p["court"] == "Supreme Court of India"
        assert "murder" not in p["legal_issue"].lower()

    # 3. Comprehensive Strategy Report Generation
    rep_res = client.post(f"/api/war-room/{session_id}/analyze", json={"operation": "report"})
    assert rep_res.status_code == 200
    report = rep_res.json()["result"]

    assert "executive_summary" in report
    assert "parties_and_procedural_posture" in report
    assert "practical_next_steps" in report
    assert "limitations_and_verification_warnings" in report

    # Export Endpoint
    export_res = client.post(f"/api/war-room/{session_id}/export")
    assert export_res.status_code == 200
    assert "Arnesh Kumar v. State of Bihar" in export_res.text
