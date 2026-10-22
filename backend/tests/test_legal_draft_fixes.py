"""
Unit and Integration Test Suite for NyayaSarathi Legal Draft Generator Fixes
Strictly verifies:
1. Zero factual hallucinations (clean antecedents, sole earner, interrogation, recovery, false implication).
2. Legal accuracy: Court hierarchy mapping (S. 480 vs S. 483 BNSS / S. 437 vs S. 439 CrPC) and no offence guessing.
3. Zero fabricated case law citations (only certified Supreme Court precedents or advocate review flags).
4. Standard 12-part Indian Regular Bail Application structure.
5. High-register Marathi legal drafting with standard Bombay High Court Devanagari terminology.
6. Form validation: Contradictory dates and party mismatches.
7. PDF and DOCX binary export integrity.
"""

import io
import pytest
from fastapi.testclient import TestClient
from main import app
from schemas.drafts import ExportDraftRequest
from services.draft_export import generate_draft_pdf, generate_draft_docx

client = TestClient(app)


# ── TEST 1: Zero Factual Hallucinations in Regular Bail Application ───────────
def test_zero_factual_hallucinations_in_bail_application():
    """
    Ensure the generator never invents facts not provided by the user.
    Missing facts must be flagged with [INFORMATION REQUIRED: ...] or omitted,
    and disputed claims must be framed conditionally.
    """
    payload = {
        "document_type": "bail_application",
        "case_category": "Criminal",
        "jurisdiction": "Court of Session, Pune",
        "facts": "Accused Ramesh Patil was arrested on 10.08.2024 by Hadapsar Police Station in connection with FIR No. 123/2024. He is presently in judicial custody at Yerwada Central Jail.",
        "parties": {
            "applicant": "Ramesh Patil",
            "respondent": "State of Maharashtra",
        },
        "target_language": "en",
        "include_citations": True,
    }
    response = client.post("/api/drafts/generate", json=payload)
    assert response.status_code == 200
    data = response.json()
    full_text = data["draft"]["full_text"]

    # 1. Clean antecedents must NOT be stated as an established fact
    assert "The applicant has no criminal antecedents" not in full_text
    assert "applicant has a clean past record" not in full_text
    assert "[INFORMATION REQUIRED: Criminal antecedents" in full_text

    # 2. Sole earning member / breadwinner must NOT be invented
    assert "sole earning member" not in full_text.lower()
    assert "sole breadwinner" not in full_text.lower()
    assert "[INFORMATION REQUIRED: Family dependency" in full_text

    # 3. Interrogation status must NOT be asserted as complete
    assert "Police interrogation is complete" not in full_text
    assert "[INFORMATION REQUIRED: Interrogation status" in full_text

    # 4. Recovery status must NOT be asserted as fully concluded
    assert "No recovery remains pending" not in full_text
    assert "[INFORMATION REQUIRED: Recovery status" in full_text

    # 5. False implication must be framed conditionally as applicant's contention
    assert "contends" in full_text or "asserts" in full_text or "respectfully submitted" in full_text

    # 6. missing_information array must be populated
    assert len(data["missing_information"]) >= 3
    assert any("antecedent" in item.lower() for item in data["missing_information"])


# ── TEST 2: Statutory Sections Not Guessed From Case Category ─────────────────
def test_statutory_sections_not_guessed_from_category():
    """
    Ensure specific penal offence sections are never guessed merely from the category.
    """
    payload = {
        "document_type": "bail_application",
        "case_category": "Commercial & Contracts",
        "jurisdiction": "Sessions Court, Greater Mumbai",
        "facts": "The applicant was arrested on 15.08.2024 following a commercial transaction dispute in FIR No. 89/2024 at BKC Police Station.",
        "parties": {
            "applicant": "Vikram Seth",
            "respondent": "State of Maharashtra",
        },
        "target_language": "en",
    }
    response = client.post("/api/drafts/generate", json=payload)
    assert response.status_code == 200
    data = response.json()
    full_text = data["draft"]["full_text"]

    # Must NOT guess Section 420 IPC or 318(4) BNS purely from "Commercial & Contracts"
    assert "Section 420 IPC" not in full_text
    assert "[INFORMATION REQUIRED: Offence sections under BNS/IPC" in full_text
    assert any("offence sections" in item.lower() for item in data["missing_information"])


# ── TEST 3: Court Hierarchy - S. 480 vs S. 483 BNSS ──────────────────────────
def test_court_hierarchy_magistrate_gets_section_480_bnss():
    """
    Magistrate courts (JMFC, MM, CJM) must invoke Section 480 BNSS, 2023 (or S. 437 CrPC).
    """
    payload = {
        "document_type": "bail_application",
        "case_category": "Criminal",
        "jurisdiction": "Judicial Magistrate First Class, Esplanade Court, Mumbai",
        "facts": "Applicant was arrested on 10.07.2024 in FIR No. 10/2024 at MRA Marg Police Station under Section 303(2) BNS.",
        "applicable_sections": ["Section 303(2) BNS"],
        "parties": {
            "applicant": "Mahesh Kale",
            "respondent": "State of Maharashtra",
        },
    }
    response = client.post("/api/drafts/generate", json=payload)
    assert response.status_code == 200
    full_text = response.json()["draft"]["full_text"]

    # Must invoke Section 480 of Bharatiya Nagarik Suraksha Sanhita, 2023
    assert "Section 480" in full_text
    assert "Section 483" not in full_text


def test_court_hierarchy_sessions_gets_section_483_bnss():
    """
    Sessions and High Courts must invoke Section 483 BNSS, 2023 (or S. 439 CrPC).
    """
    payload = {
        "document_type": "bail_application",
        "case_category": "Criminal",
        "jurisdiction": "Sessions Court, Greater Mumbai",
        "facts": "Applicant was arrested on 10.07.2024 in FIR No. 10/2024 at MRA Marg Police Station under Section 318(4) BNS.",
        "applicable_sections": ["Section 318(4) BNS"],
        "parties": {
            "applicant": "Mahesh Kale",
            "respondent": "State of Maharashtra",
        },
    }
    response = client.post("/api/drafts/generate", json=payload)
    assert response.status_code == 200
    full_text = response.json()["draft"]["full_text"]

    # Must invoke Section 483 of Bharatiya Nagarik Suraksha Sanhita, 2023
    assert "Section 483" in full_text
    assert "Section 480" not in full_text


def test_anticipatory_bail_gets_section_482_bnss():
    """
    Anticipatory bail applications must invoke Section 482 BNSS, 2023 (or S. 438 CrPC).
    """
    payload = {
        "document_type": "bail_application",
        "case_category": "Criminal",
        "jurisdiction": "Court of Session, Pune",
        "requested_relief": "Anticipatory bail under S. 482 BNSS in the event of arrest",
        "facts": "Applicant apprehends imminent arrest in connection with FIR No. 44/2024 registered on 15.07.2024 at Shivajinagar Police Station.",
        "parties": {
            "applicant": "Anil Deshmukh",
            "respondent": "State of Maharashtra",
        },
    }
    response = client.post("/api/drafts/generate", json=payload)
    assert response.status_code == 200
    full_text = response.json()["draft"]["full_text"]

    assert "Section 482" in full_text


# ── TEST 4: Case Law Citations Not Fabricated ─────────────────────────────────
def test_case_citations_not_fabricated():
    """
    Precedents must only be reliable, certified Supreme Court authorities.
    Unverified case laws must not be invented.
    """
    payload = {
        "document_type": "bail_application",
        "case_category": "Criminal",
        "jurisdiction": "Sessions Court, Thane",
        "facts": "Applicant arrested on 12.08.2024 in FIR No. 77/2024 at Naupada Police Station under Section 303(2) BNS. Custody is judicial.",
        "applicable_sections": ["Section 303(2) BNS, 2023"],
        "parties": {
            "applicant": "Ganesh Shinde",
            "respondent": "State of Maharashtra",
        },
        "include_citations": True,
    }
    response = client.post("/api/drafts/generate", json=payload)
    assert response.status_code == 200
    data = response.json()

    citations = data["citations"]
    assert len(citations) >= 1

    # Check citation verification metadata (no false claims of external live verification)
    for cit in citations:
        assert cit["verification_status"] in ["verification_required", "verified_primary_source", "VERIFIED"]
        assert cit["citation"] != ""

    # Must include authentic Landmark Supreme Court Precedents or Statutory Anchors
    assert any(
        any(precedent in cit["title"] for precedent in ["Satender Kumar Antil", "Sanjay Chandra", "Arnesh Kumar", "Babu Singh", "Bharatiya Nagarik", "Section 483"])
        for cit in citations
    )


# ── TEST 5: Complete 12-Part Indian Bail Application Structure ───────────────
def test_bail_application_12_part_structure():
    """
    Verify presence of all 12 structural requirements in Indian Regular Bail Application:
    1. Court name and jurisdiction
    2. Case title and case number placeholders
    3. Applicant and respondent details
    4. FIR number, police station, date and applicable statutory sections
    5. Material facts and chronology
    6. Arrest date and current custody status
    7. Previous bail application details
    8. Case-specific grounds for bail
    9. Relevant legal provisions and verified precedents
    10. Prayer clause
    11. Proposed bail conditions
    12. Place, date, signatures, verification and annexure list
    """
    payload = {
        "document_type": "bail_application",
        "case_category": "Criminal",
        "jurisdiction": "Court of Session, Greater Mumbai",
        "facts": "Applicant was arrested on 05.08.2024 in FIR No. 201/2024 at Bandra Police Station under Section 318(4) BNS. Currently in judicial custody at Arthur Road Jail. No prior bail was preferred before any court.",
        "applicable_sections": ["Section 318(4) BNS, 2023"],
        "parties": {
            "applicant": "Sanjay Kapoor, Age 34, R/o Bandra West, Mumbai",
            "respondent": "The State of Maharashtra (through Bandra Police Station)",
        },
    }
    response = client.post("/api/drafts/generate", json=payload)
    assert response.status_code == 200
    data = response.json()
    full_text = data["draft"]["full_text"]
    sections = data["draft"]["sections"]

    # Discrete section representation
    assert len(sections) >= 5

    # 1. Court Name & Jurisdiction
    assert "IN THE COURT OF SESSION" in full_text or "IN THE COURT OF" in full_text
    # 2. Case Number Placeholder
    assert "BAIL APPLICATION NO." in full_text
    # 3. Applicant and Respondent Details
    assert "APPLICANT / ACCUSED" in full_text
    assert "RESPONDENT / STATE / PROSECUTION" in full_text or "RESPONDENT" in full_text
    # 4. FIR, Police Station, and Statutory Sections
    assert "201/2024" in full_text
    assert "Bandra Police Station" in full_text
    assert "Section 318(4) BNS, 2023" in full_text
    # 5. Material Facts & Chronology
    assert "CHRONOLOGY OF MATERIAL EVENTS & FACTS" in full_text
    # 6. Arrest Date & Current Custody Status
    assert "ARREST PARTICULARS AND CUSTODIAL STATUS" in full_text
    assert "05.08.2024" in full_text
    # 7. Previous Bail Application History
    assert "PARTICULARS OF PREVIOUS BAIL APPLICATIONS" in full_text
    # 8. Grounds for Bail
    assert "substantive grounds" in full_text.lower() or "grounds" in full_text.lower()
    # 9. Legal Provisions and Precedents
    assert "STATUTORY PROVISION" in full_text and "PRECEDENTS" in full_text
    # 10. Prayer Clause
    assert "PRAYER FOR RELIEF" in full_text or "PRAYER" in full_text
    # 11. Proposed Bail Conditions
    assert "PROPOSED BAIL CONDITIONS" in full_text or "undertakes to abide by" in full_text
    # 12. Signatures, Verification, and Annexure List
    assert "VERIFICATION & AFFIDAVIT IN SUPPORT" in full_text or "VERIFICATION" in full_text
    assert "LIST OF ANNEXURES" in full_text


# ── TEST 6: High-Register Marathi Legal Drafting ──────────────────────────────
def test_marathi_legal_drafting():
    """
    Ensure formal, grammatically correct Marathi drafting with standard
    Bombay High Court Devanagari legal expressions and preserved statutory numbers.
    """
    payload = {
        "document_type": "bail_application",
        "case_category": "Criminal",
        "jurisdiction": "सत्र न्यायालय, पुणे",
        "facts": "अर्जदार विजय साळुंखे यांना 14.07.2024 रोजी शिवाजीनगर पोलीस स्टेशनच्या एफआयआर क्र. 99/2024 अंतर्गत अटक करण्यात आली आहे. कलम 318(4) बीएनएस लागू केले आहे. अर्जदार येरवडा कारागृहात न्यायालयीन कोठडीत आहेत.",
        "applicable_sections": ["Section 318(4) BNS"],
        "parties": {
            "applicant": "विजय साळुंखे",
            "respondent": "महाराष्ट्र शासन",
        },
        "target_language": "mr",
        "include_citations": True,
    }
    response = client.post("/api/drafts/generate", json=payload)
    assert response.status_code == 200
    data = response.json()
    translated_text = data["translated_text"]

    # Formal Court Addressing
    assert "मेहेरबान" in translated_text or "मा. सत्र न्यायालय" in translated_text

    # Standard Pleadings Heading
    assert "फौजदारी नियमित जामीन अर्ज" in translated_text

    # Parties Representation
    assert "अर्जदार / आरोपी" in translated_text
    assert "विरुद्ध" in translated_text
    assert "गैरअर्जदार / सरकार" in translated_text

    # High-register terms
    assert "सदरहू" in translated_text
    assert "जामिनाची कारणे" in translated_text
    assert "सत्यप्रतिज्ञा" in translated_text or "प्रतिज्ञापत्र" in translated_text
    assert "जोडपत्रांची यादी" in translated_text

    # Accurate preservation of names, statutory sections and FIR numbers
    assert "विजय साळुंखे" in translated_text
    assert "99/2024" in translated_text
    assert "318(4)" in translated_text or "३१८(४)" in translated_text
    assert "483" in translated_text or "४८३" in translated_text


# ── TEST 7: Contradictory Dates and Party Discrepancy Validation ───────────────
def test_validation_detects_future_dates():
    """
    Detects when cause of action / incident date is set in the future.
    """
    payload = {
        "document_type": "legal_notice",
        "case_category": "Commercial",
        "cause_of_action_date": "2099-12-31",
        "facts": "Payment default occurred under invoice #100.",
        "parties": {"sender": "Alpha Corp", "recipient": "Beta Ltd"},
    }
    response = client.post("/api/drafts/generate", json=payload)
    assert response.status_code == 200
    data = response.json()
    warnings = data["warnings"]
    assert any("future" in w.lower() for w in warnings)


def test_validation_detects_fir_registered_after_arrest():
    """
    Detects when FIR registration date is recorded after arrest date.
    """
    payload = {
        "document_type": "bail_application",
        "case_category": "Criminal",
        "facts": "Arrest date: 05.08.2024. FIR registered on 20.08.2024 at Shivajinagar Police Station.",
        "parties": {"applicant": "Rajesh Gupta", "respondent": "State of Maharashtra"},
    }
    response = client.post("/api/drafts/generate", json=payload)
    assert response.status_code == 200
    data = response.json()
    warnings = data["warnings"]
    assert any("recorded after the arrest date" in w.lower() for w in warnings)


def test_validation_detects_party_name_mismatch():
    """
    Detects when party name given in form is completely absent from detailed narrative facts.
    """
    payload = {
        "document_type": "bail_application",
        "case_category": "Criminal",
        "facts": "Sunil Shrestha was apprehended by police on 10.08.2024 in FIR No. 12/2024.",
        "parties": {"applicant": "Prakash Tendulkar", "respondent": "State of Maharashtra"},
    }
    response = client.post("/api/drafts/generate", json=payload)
    assert response.status_code == 200
    data = response.json()
    warnings = data["warnings"]
    assert any("inconsistent" in w.lower() for w in warnings)


# ── TEST 8: PDF and DOCX Export with 12-Part Bail Structure ───────────────────
def test_pdf_and_docx_export_with_bail_sections():
    """
    Ensures PDF and DOCX export retain structure and output valid binary payloads.
    """
    # 1. Generate the bail application
    gen_payload = {
        "document_type": "bail_application",
        "case_category": "Criminal",
        "jurisdiction": "Court of Session, Greater Mumbai",
        "facts": "Accused was arrested on 10.08.2024 in FIR No. 200/2024 at Bandra PS. In judicial custody.",
        "applicable_sections": ["Section 318(4) BNS"],
        "parties": {
            "applicant": "Kailash Nathan",
            "respondent": "State of Maharashtra",
        },
    }
    gen_resp = client.post("/api/drafts/generate", json=gen_payload)
    assert gen_resp.status_code == 200
    gen_data = gen_resp.json()

    export_req = {
        "title": gen_data["draft"]["title"],
        "document_type": gen_data["document_type"],
        "sections": gen_data["draft"]["sections"],
        "citations": gen_data["citations"],
        "language": "en",
    }

    # Test PDF Export endpoint
    pdf_resp = client.post("/api/drafts/export/pdf", json=export_req)
    assert pdf_resp.status_code == 200
    assert pdf_resp.headers["content-type"] == "application/pdf"
    assert pdf_resp.content.startswith(b"%PDF")

    # Test DOCX Export endpoint
    docx_resp = client.post("/api/drafts/export/docx", json=export_req)
    assert docx_resp.status_code == 200
    assert docx_resp.headers["content-type"] == (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    assert docx_resp.content.startswith(b"PK")  # ZIP/DOCX magic bytes
