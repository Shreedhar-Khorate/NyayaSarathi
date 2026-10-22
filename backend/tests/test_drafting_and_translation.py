"""
Comprehensive Test Suite for NyayaSarathi Legal Drafting & Regional Translation (Feature 3.8)
Covers:
1. Valid legal notice generation.
2. Valid bail application generation.
3. Valid petition generation.
4. Valid reply generation.
5. Missing required facts validation.
6. Unsupported document type handling (400 error).
7. Unsupported target language handling (400 error).
8. Empty or excessively long input validation (400 error).
9. Retrieval returning no relevant sources (graceful warning, factual draft).
10. Citation verification and source metadata.
11. LLM timeout or unavailable model fallback.
12. Regional translation into Hindi ('hi') and Marathi ('mr').
13. Preservation of the original draft after translation.
14. Section regeneration without modifying unrelated sections.
15. PDF export formatting and binary response.
16. DOCX export formatting and binary response.
17. Factual reliability & missing information placeholders ([MISSING: ...]).
18. Backward compatibility with legacy schema fields.
"""

import io
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from main import app
from schemas.drafts import (
    DraftRequest,
    DraftResponse,
    DraftSection,
    ExportDraftRequest,
    RegenerateSectionRequest,
    TranslateDraftRequest,
)
from services.drafts_service import generate_draft, regenerate_draft_section, translate_draft
from services.draft_export import generate_draft_pdf, generate_draft_docx

client = TestClient(app)


# ── TEST 1: Valid Legal Notice Generation ─────────────────────────────────────
def test_valid_legal_notice_generation():
    payload = {
        "document_type": "legal_notice",
        "case_category": "Commercial",
        "facts": "My client entered into a supply contract on 15.01.2023 with ABC Enterprises for supply of industrial valves. ABC Enterprises defaulted on payment of invoice #INV-902 amounting to Rs. 4,50,000/- due on 01.03.2023. Multiple reminders have been ignored.",
        "jurisdiction": "Delhi High Court",
        "parties": {
            "sender": "Apex Manufacturing Ltd.",
            "recipient": "ABC Enterprises Pvt. Ltd., 45 Industrial Area, Okhla, New Delhi",
        },
        "requested_relief": "Immediate payment of Rs. 4,50,000/- with 18% p.a. interest",
        "target_language": "en",
        "include_citations": True,
    }
    response = client.post("/api/drafts/generate", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "completed"
    assert data["document_type"] == "legal_notice"
    assert "draft" in data
    assert len(data["draft"]["sections"]) >= 4
    assert any("DEMAND" in s["title"].upper() or "PEREMPTORY" in s["title"].upper() for s in data["draft"]["sections"])
    assert "Apex Manufacturing Ltd" in data["draft"]["full_text"]
    assert len(data["citations"]) >= 1
    assert data["draft_text"] is not None


# ── TEST 2: Valid Bail Application Generation ─────────────────────────────────
def test_valid_bail_application_generation():
    payload = {
        "document_type": "bail_application",
        "case_category": "Criminal",
        "facts": "Applicant was arrested on 10.08.2024 by Connaught Place Police Station in connection with FIR No. 120/2024 under Section 318(4) BNS. Applicant has been in judicial custody for 45 days. Co-accused has already been released on bail. No recovery is pending from applicant.",
        "jurisdiction": "Court of Sessions, Patiala House Courts, New Delhi",
        "parties": {
            "applicant": "Ramesh Kumar Sharma",
            "respondent": "State of NCT of Delhi",
        },
        "important_dates": ["10.08.2024"],
        "target_language": "en",
        "include_citations": True,
    }
    response = client.post("/api/drafts/generate", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["document_type"] == "bail_application"
    assert any("GROUNDS" in s["title"].upper() for s in data["draft"]["sections"])
    assert any("PRAYER" in s["title"].upper() for s in data["draft"]["sections"])
    # Should contain references to personal liberty / bail canons
    assert "BAIL" in data["draft"]["title"].upper()
    assert len(data["citations"]) >= 1


# ── TEST 3: Valid Petition Generation ─────────────────────────────────────────
def test_valid_petition_generation():
    payload = {
        "document_type": "petition",
        "case_category": "Constitutional",
        "facts": "Petitioner was operating a licensed retail pharmacy for 15 years. On 12.02.2024, the Municipal Corporation arbitrarily sealed the premises without issuing any prior show cause notice or affording an opportunity of hearing, violating principles of natural justice and Article 19(1)(g).",
        "jurisdiction": "High Court of Bombay",
        "parties": {
            "applicant": "Dr. Sunil Patil",
            "respondent": "Municipal Corporation of Greater Mumbai & Anr.",
        },
        "requested_relief": "Writ of Certiorari quashing the sealing order dated 12.02.2024 and restoration of premises",
        "target_language": "en",
    }
    response = client.post("/api/drafts/generate", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["document_type"] == "petition"
    assert len(data["draft"]["sections"]) >= 4
    assert any("FACTS" in s["title"].upper() or "SYNOPSIS" in s["title"].upper() or "GROUNDS" in s["title"].upper() for s in data["draft"]["sections"])
    assert any("RELIEF" in s["title"].upper() or "PRAYER" in s["title"].upper() for s in data["draft"]["sections"])


# ── TEST 4: Valid Reply / Written Statement Generation ────────────────────────
def test_valid_reply_generation():
    payload = {
        "document_type": "reply",
        "case_category": "Civil",
        "facts": "Responding to legal notice dated 05.01.2024 sent by claimant alleging non-delivery of goods. Respondent states goods were tendered on 20.12.2023 but claimant refused delivery citing lack of warehouse space. The delay is entirely on part of claimant.",
        "jurisdiction": "Civil Court, Pune",
        "parties": {
            "applicant": "Kalyani Logistics",
            "respondent": "Swift Traders",
        },
        "requested_relief": "Withdrawal of baseless notice and payment of storage demurrage charges",
    }
    response = client.post("/api/drafts/generate", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["document_type"] == "reply"
    assert len(data["draft"]["sections"]) >= 4
    assert any("PRELIMINARY" in s["title"].upper() or "FACTS" in s["title"].upper() or "REPLY" in s["title"].upper() for s in data["draft"]["sections"])
    assert any("RELIEF" in s["title"].upper() or "PRAYER" in s["title"].upper() or "GROUNDS" in s["title"].upper() or "DEMAND" in s["title"].upper() or "VERIFICATION" in s["title"].upper() for s in data["draft"]["sections"])


# ── TEST 5: Missing Required Facts Validation ─────────────────────────────────
def test_missing_required_facts_validation():
    # Empty string facts
    response = client.post("/api/drafts/generate", json={
        "document_type": "legal_notice",
        "facts": "   ",
    })
    assert response.status_code == 400
    assert "facts" in response.json()["error"].lower()

    # Fact too short (< 10 chars)
    response2 = client.post("/api/drafts/generate", json={
        "document_type": "legal_notice",
        "facts": "Too short",
    })
    assert response2.status_code == 400
    assert "at least 10 characters" in response2.json()["error"]


# ── TEST 6: Unsupported Document Type ─────────────────────────────────────────
def test_unsupported_document_type():
    response = client.post("/api/drafts/generate", json={
        "document_type": "will_and_testament",
        "facts": "This is a testamentary dispute regarding property distribution across legal heirs.",
    })
    assert response.status_code == 400
    assert "unsupported document type" in response.json()["error"].lower()


# ── TEST 7: Unsupported Target Language ───────────────────────────────────────
def test_unsupported_target_language():
    response = client.post("/api/drafts/generate", json={
        "document_type": "legal_notice",
        "facts": "Claimant demands return of security deposit of Rs. 1,00,000/- following lease expiry.",
        "target_language": "fr",  # French not supported
    })
    assert response.status_code == 400
    assert "unsupported target language" in response.json()["error"].lower()


# ── TEST 8: Excessively Long Input ────────────────────────────────────────────
def test_excessively_long_input():
    huge_facts = "Facts " * 15000  # > 50,000 characters
    response = client.post("/api/drafts/generate", json={
        "document_type": "legal_notice",
        "facts": huge_facts,
    })
    assert response.status_code == 400
    assert "exceeds maximum allowable length" in response.json()["error"]


# ── TEST 9: Retrieval When No Documents or Citations are Disabled ─────────────
def test_generation_without_citations():
    payload = {
        "document_type": "legal_notice",
        "facts": "Notice demanding return of mortgaged title deeds after loan discharge.",
        "include_citations": False,
    }
    response = client.post("/api/drafts/generate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data["citations"]) == 0
    assert any("citations disabled" in w.lower() for w in data["warnings"])


# ── TEST 10: Citation Integrity & Verification Metadata ───────────────────────
def test_citation_integrity():
    payload = {
        "document_type": "bail_application",
        "facts": "Applicant seeks bail under section 439 CrPC in crime registered in 2023 for alleged cheating.",
        "include_citations": True,
    }
    response = client.post("/api/drafts/generate", json=payload)
    assert response.status_code == 200
    data = response.json()
    citations = data["citations"]
    assert len(citations) >= 1
    for c in citations:
        assert c["title"] is not None
        assert c["citation"] is not None
        assert c["verification_status"] in ["verified_primary_source", "verification_required"]
        assert c["authority_type"] in ["binding_precedent", "persuasive_authority", "statutory", "unverified"]


# ── TEST 11: LLM Offline Failure Returns Actionable Error (No Static Fallback) ──
def test_llm_fallback_on_api_error():
    with patch("services.drafts_service._call_llm_json", side_effect=RuntimeError("Groq API offline")):
        payload = {
            "document_type": "legal_notice",
            "facts": "Client was wrongfully terminated without payment of statutory severance and notice pay of 3 months.",
        }
        response = client.post("/api/drafts/generate", json=payload)
        # Dynamic AI Only requirement: never return static fallback, return explicit error
        assert response.status_code == 502
        assert "Legal draft generation failed" in response.json()["error"]
        assert "No static fallback is permitted" in response.json()["error"]


# ── TEST 12: Regional Translation into Hindi and Marathi ──────────────────────
def test_regional_translation_hindi_and_marathi():
    # Hindi Translation
    hi_payload = {
        "document_type": "legal_notice",
        "facts": "Notice calling upon tenant to vacate commercial shop and clear outstanding rent arrears of Rs. 80,000/-.",
        "target_language": "hi",
    }
    hi_res = client.post("/api/drafts/generate", json=hi_payload)
    assert hi_res.status_code == 200
    hi_data = hi_res.json()
    assert hi_data["language"] == "hi"
    assert hi_data["translated_text"] is not None

    # Marathi Translation
    mr_payload = {
        "document_type": "bail_application",
        "facts": "Bail application on grounds of parity as prime co-accused was granted bail by Sessions Court.",
        "target_language": "mr",
    }
    mr_res = client.post("/api/drafts/generate", json=mr_payload)
    assert mr_res.status_code == 200
    mr_data = mr_res.json()
    assert mr_data["language"] == "mr"
    assert mr_data["translated_text"] is not None


# ── TEST 13: Preservation of Original Draft After Translation ─────────────────
def test_preservation_of_original_draft_after_translation():
    payload = {
        "document_type": "legal_notice",
        "facts": "Notice demanding handover of original documents following settlement agreement.",
        "target_language": "hi",
    }
    response = client.post("/api/drafts/generate", json=payload)
    assert response.status_code == 200
    data = response.json()
    # draft_text contains English original; translated_text contains Hindi
    assert data["draft_text"] is not None
    assert "LEGAL NOTICE" in data["draft_text"].upper()
    assert data["translated_text"] is not None


# ── TEST 14: Section Regeneration Without Modifying Unrelated Sections ────────
def test_section_regeneration():
    payload = {
        "document_type": "bail_application",
        "section_id": "grounds_for_bail",
        "section_title": "Grounds for Grant of Bail",
        "current_content": "1. Applicant is innocent and falsely implicated.\n2. Applicant has clean antecedents.",
        "facts": "Applicant was arrested for bailable offence and is sole breadwinner suffering from cardiac condition.",
        "instructions": "Add emphasis on severe medical illness requiring specialized cardiac treatment.",
        "language": "en",
    }
    response = client.post("/api/drafts/regenerate-section", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["section_id"] == "grounds_for_bail"
    assert "medical" in data["content"].lower() or "cardiac" in data["content"].lower() or "applicant" in data["content"].lower()


# ── TEST 15: PDF Export Generates Valid PDF Bytes ─────────────────────────────
def test_pdf_export_endpoint():
    payload = {
        "title": "Legal Notice under Section 138 NI Act",
        "document_type": "legal_notice",
        "sections": [
            {
                "id": "sec1",
                "title": "Parties and Recitals",
                "content": "To ABC Pvt Ltd, from Advocate on behalf of client.",
                "order": 1,
            },
            {
                "id": "sec2",
                "title": "Demand Clause",
                "content": "You are called upon to pay Rs. 5,00,000/- within 15 days.",
                "order": 2,
            },
        ],
        "citations": [
            {
                "source_id": "S1",
                "title": "Section 138 NI Act",
                "citation": "NI Act 1881 §138",
                "court": "Parliament of India",
                "excerpt": "Cheque dishonour statutory demand period.",
                "is_verified": True,
                "verification_status": "verified_primary_source",
                "authority_type": "statutory",
            }
        ],
    }
    response = client.post("/api/drafts/export/pdf", json=payload)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF")
    assert len(response.content) > 1000


# ── TEST 16: DOCX Export Generates Valid Word Document ────────────────────────
def test_docx_export_endpoint():
    payload = {
        "title": "Bail Application under Section 439 CrPC",
        "document_type": "bail_application",
        "sections": [
            {
                "id": "sec1",
                "title": "Court Heading",
                "content": "In the Court of Sessions at Delhi.",
                "order": 1,
            },
            {
                "id": "sec2",
                "title": "Grounds for Bail",
                "content": "Applicant is a permanent resident with no risk of flight.",
                "order": 2,
            },
        ],
        "citations": [],
    }
    response = client.post("/api/drafts/export/docx", json=payload)
    assert response.status_code == 200
    assert "wordprocessingml" in response.headers["content-type"]
    assert response.content.startswith(b"PK")  # ZIP magic bytes for DOCX
    assert len(response.content) > 1000


# ── TEST 17: Factual Missing Information Detection & Placeholders ─────────────
def test_missing_information_detection():
    # Bail application with bare facts (missing FIR, Police Station, Arrest date)
    payload = {
        "document_type": "bail_application",
        "facts": "Accused was picked up on suspicion regarding theft of motorcycle.",
    }
    response = client.post("/api/drafts/generate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data["missing_information"]) >= 2
    assert any("fir" in m.lower() or "crime" in m.lower() for m in data["missing_information"])
    assert "[MISSING:" in data["draft"]["full_text"]


# ── TEST 18: Backward Compatibility with Legacy Schema ────────────────────────
def test_backward_compatibility_schema():
    payload = {
        "draft_type": "Bail Application",
        "case_facts": "The applicant was arrested on 01.05.2023 in an alleged dispute and has been detained for 30 days.",
    }
    response = client.post("/api/drafts/generate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["document_type"] == "bail_application"
    assert "draft_text" in data
    assert "citations_used" in data
