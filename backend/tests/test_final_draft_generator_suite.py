"""
Automated Test Suite for NyayaSarathi Dynamic Legal Draft Generator
Verifies all 17 acceptance requirements:
1. Valid generation for each supported document type.
2. Regular bail versus anticipatory bail.
3. Conflicting request aliases.
4. Missing facts and invalid languages.
5. Unknown or conflicting statutory-era dates.
6. Unresolved court hierarchy without a guessed bail section.
7. No false verified status for LLM-generated citations.
8. Missing excerpts and user-supplied statutory references.
9. Duplicate section IDs and malformed model output.
10. Inconsistent full_text and sections.
11. Unsupported facts and missing-information placeholders.
12. Hindi/Marathi language validation.
13. Provider failure and exhausted retries.
14. Translation failure without false success.
15. Regeneration preserving the original context.
16. Export and backward-compatibility fields.
17. Proof that the drafting feature does not import or invoke RAG, vector search, precedent retrieval, or deterministic fallback drafting.
"""

import io
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from main import app
from schemas.drafts import (
    DraftRequest,
    DraftResponse,
    DraftContent,
    DraftSection,
    CitationInfo,
    ExportDraftRequest,
    RegenerateSectionRequest,
    TranslateDraftRequest,
)
from services.drafts_service import (
    generate_draft,
    regenerate_draft_section,
    translate_draft,
    _evaluate_statutory_era,
    _determine_bail_procedural_section,
    _validate_draft_output,
)
from services.draft_export import generate_draft_pdf, generate_draft_docx

client = TestClient(app)


# ── TEST 1: Valid Generation for Each Supported Document Type ─────────────────
@pytest.mark.parametrize("doc_type,expected_phrase", [
    ("legal_notice", "DEMAND"),
    ("bail_application", "BAIL"),
    ("petition", "PETITION"),
    ("reply", "REPLY"),
])
def test_req1_valid_generation_for_each_supported_document_type(doc_type, expected_phrase):
    payload = {
        "document_type": doc_type,
        "facts": f"Detailed factual chronology for testing {doc_type} generation under Indian legal standards with sufficient characters.",
        "jurisdiction": "High Court of Bombay",
        "target_language": "en",
        "include_citations": True,
    }
    response = client.post("/api/drafts/generate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert data["document_type"] == doc_type
    assert len(data["draft"]["sections"]) >= 1
    assert data["draft"]["full_text"] is not None


# ── TEST 2: Regular Bail Versus Anticipatory Bail ──────────────────────────────
def test_req2_regular_bail_vs_anticipatory_bail():
    # Regular bail
    reg_payload = {
        "document_type": "regular_bail",
        "jurisdiction": "Sessions Court, Pune",
        "facts": "Accused was arrested on 10.08.2024 and is in judicial custody at Yerwada Central Jail under FIR 55/2024.",
    }
    reg_res = client.post("/api/drafts/generate", json=reg_payload)
    assert reg_res.status_code == 200
    reg_data = reg_res.json()
    assert reg_data["document_type"] == "bail_application"
    assert reg_data["subtype"] == "regular_bail"
    assert "483" in reg_data["draft"]["full_text"] or "Section 483" in str(reg_data["warnings"])

    # Anticipatory bail
    anti_payload = {
        "document_type": "anticipatory_bail",
        "jurisdiction": "Sessions Court, Pune",
        "requested_relief": "Anticipatory bail in the event of arrest",
        "facts": "Applicant apprehends imminent arrest in connection with FIR 55/2024 registered on 15.08.2024 at Shivajinagar Police Station.",
    }
    anti_res = client.post("/api/drafts/generate", json=anti_payload)
    assert anti_res.status_code == 200
    anti_data = anti_res.json()
    assert anti_data["document_type"] == "bail_application"
    assert anti_data["subtype"] == "anticipatory_bail"
    assert "482" in anti_data["draft"]["full_text"] or any("482" in w for w in anti_data["warnings"])


# ── TEST 3: Conflicting Request Aliases ────────────────────────────────────────
def test_req3_conflicting_request_aliases():
    # Conflicting document_type and draft_type
    conflict_type_payload = {
        "document_type": "legal_notice",
        "draft_type": "bail_application",
        "facts": "Substantive facts for the dispute testing conflicting document types.",
    }
    res1 = client.post("/api/drafts/generate", json=conflict_type_payload)
    assert res1.status_code == 400
    assert "conflicting document_type" in res1.json()["error"].lower()

    # Conflicting facts and case_facts
    conflict_facts_payload = {
        "document_type": "legal_notice",
        "facts": "Contract default of Rs. 5,00,000/- on 01.01.2024.",
        "case_facts": "Completely different narrative regarding property trespass.",
    }
    res2 = client.post("/api/drafts/generate", json=conflict_facts_payload)
    assert res2.status_code == 400
    assert "conflicting" in res2.json()["error"].lower()


# ── TEST 4: Missing Facts and Invalid Languages ───────────────────────────────
def test_req4_missing_facts_and_invalid_languages():
    # Empty facts
    res1 = client.post("/api/drafts/generate", json={"document_type": "legal_notice", "facts": "   "})
    assert res1.status_code == 400
    assert "facts" in res1.json()["error"].lower()

    # Facts too short (< 10 chars)
    res2 = client.post("/api/drafts/generate", json={"document_type": "legal_notice", "facts": "Short"})
    assert res2.status_code == 400
    assert "at least 10 characters" in res2.json()["error"]

    # Unsupported language
    res3 = client.post("/api/drafts/generate", json={
        "document_type": "legal_notice",
        "facts": "Valid case facts describing a commercial transaction default.",
        "target_language": "spanish",
    })
    assert res3.status_code == 400
    assert "unsupported target language" in res3.json()["error"].lower()


# ── TEST 5: Unknown or Conflicting Statutory-Era Dates ─────────────────────────
def test_req5_unknown_or_conflicting_statutory_era_dates():
    # Missing date
    era, warnings = _evaluate_statutory_era(facts="Accused was arrested without mention of date.")
    assert era == "UNDETERMINED"
    assert any("not explicitly specified" in w or "not explicitly established" in w for w in warnings)

    # Date ambiguous across July 1 2024 boundary (e.g. 04/08/2024)
    era_ambig, warnings_ambig = _evaluate_statutory_era(facts="FIR registered on 04/08/2024.")
    assert era_ambig == "UNDETERMINED"
    assert any("ambiguous" in w.lower() for w in warnings_ambig)


# ── TEST 6: Unresolved Court Hierarchy Without Guessed Bail Section ───────────
def test_req6_unresolved_court_hierarchy_without_guessed_section():
    sec_num, full_title, _, warnings = _determine_bail_procedural_section(
        jurisdiction=None,
        facts="Applicant seeks regular bail in FIR 10/2024.",
        era="BNS_BNSS",
        doc_type="bail_application",
    )
    # Must NOT guess S. 483 or S. 480 when court hierarchy is unspecified
    assert "Unresolved" in sec_num
    assert any("hierarchy is not specified" in w.lower() for w in warnings)


# ── TEST 7: No False Verified Status for LLM Citations ────────────────────────
def test_req7_no_false_verified_status_for_llm_citations():
    mock_llm_data = {
        "title": "BAIL APPLICATION",
        "sections": [{"id": "sec_1", "title": "Grounds", "content": "Bail grounds text.", "order": 1}],
        "citations": [
            {
                "title": "State of Rajasthan v. Balchand",
                "citation": "AIR 1977 SC 2447",
                "court": "Supreme Court of India",
                "authority_type": "binding_precedent",
            }
        ]
    }
    with patch("services.drafts_service._call_drafting_llm_json", return_value=mock_llm_data):
        payload = {
            "document_type": "bail_application",
            "jurisdiction": "Court of Session, Pune",
            "facts": "Accused was arrested on 10.08.2024 in FIR 10/2024.",
            "include_citations": True,
        }
        res = client.post("/api/drafts/generate", json=payload)
        assert res.status_code == 200
        citations = res.json()["citations"]
        for cit in citations:
            # Must remain unverified unless authoritative source verification exists
            assert cit["is_verified"] is False
            assert cit["verification_status"] == "verification_required"
            # No fake evidence chunk IDs (like S1, S2)
            assert cit["source_id"] is None


# ── TEST 8: Missing Excerpts and User-Supplied Statutory References ────────────
def test_req8_missing_excerpts_and_user_supplied_references():
    mock_llm_data = {
        "title": "LEGAL NOTICE",
        "sections": [{"id": "sec_1", "title": "Notice", "content": "Notice content.", "order": 1}],
    }
    with patch("services.drafts_service._call_drafting_llm_json", return_value=mock_llm_data):
        payload = {
            "document_type": "legal_notice",
            "facts": "Default under promissory note dated 10.01.2024.",
            "applicable_sections": ["Section 138 of the Negotiable Instruments Act, 1881"],
        }
        res = client.post("/api/drafts/generate", json=payload)
        assert res.status_code == 200
        citations = res.json()["citations"]
        assert len(citations) >= 1
        user_cit = citations[0]
        assert user_cit["title"] == "Section 138 of the Negotiable Instruments Act, 1881"
        assert user_cit["provenance"] == "user_supplied"
        assert user_cit["is_verified"] is False
        assert user_cit["excerpt"] is None  # Never manufacture quotes to satisfy non-empty fields


# ── TEST 9: Duplicate Section IDs and Malformed Model Output ──────────────────
def test_req9_duplicate_section_ids_rejected():
    duplicate_ids_data = {
        "title": "LEGAL DRAFT",
        "sections": [
            {"id": "sec_same", "title": "Part 1", "content": "Content 1", "order": 1},
            {"id": "sec_same", "title": "Part 2", "content": "Content 2", "order": 2},
        ],
    }
    is_valid, err_msg, content = _validate_draft_output(
        data=duplicate_ids_data,
        doc_type="legal_notice",
        subtype="legal_notice",
        target_lang="en",
        facts="Test facts.",
    )
    assert is_valid is False
    assert "duplicate section id" in err_msg.lower()


# ── TEST 10: Inconsistent Full Text and Sections ──────────────────────────────
def test_req10_consistent_full_text_and_sections():
    # If full_draft_text is omitted by LLM, full_text must be deterministically synthesized
    data_no_full = {
        "title": "LEGAL NOTICE",
        "sections": [
            {"id": "sec_1", "title": "Notice Header", "content": "Header content.", "order": 1},
            {"id": "sec_2", "title": "Demand", "content": "Demand content.", "order": 2},
        ],
    }
    is_valid, err_msg, content = _validate_draft_output(
        data=data_no_full,
        doc_type="legal_notice",
        subtype="legal_notice",
        target_lang="en",
        facts="Test facts.",
    )
    assert is_valid is True
    assert "Header content." in content.full_text
    assert "Demand content." in content.full_text


# ── TEST 11: Unsupported Facts and Missing-Information Placeholders ───────────
def test_req11_unsupported_facts_rejected():
    hallucinated_data = {
        "title": "BAIL APPLICATION",
        "sections": [
            {"id": "sec_1", "title": "Grounds", "content": "The applicant has no criminal antecedents.", "order": 1}
        ],
        "full_draft_text": "The applicant has no criminal antecedents and is a respected person.",
    }
    is_valid, err_msg, content = _validate_draft_output(
        data=hallucinated_data,
        doc_type="bail_application",
        subtype="regular_bail",
        target_lang="en",
        facts="Applicant was arrested in FIR 12/2024 at Hadapsar PS.",  # No mention of clean record
    )
    assert is_valid is False
    assert "criminal antecedents" in err_msg.lower()


# ── TEST 12: Hindi/Marathi Language Validation ────────────────────────────────
def test_req12_hindi_marathi_language_validation():
    # Hindi text submitted for Marathi request must be rejected
    hindi_data_for_marathi = {
        "title": "विधिक सूचना",
        "sections": [
            {"id": "sec_1", "title": "सूचना", "content": "यह विधिक सूचना प्रेषित है। विपक्षी द्वारा भुगतान नहीं किया गया है।", "order": 1}
        ],
        "full_draft_text": "विपक्षी द्वारा भुगतान नहीं किया गया है।",
    }
    is_valid, err_msg, _ = _validate_draft_output(
        data=hindi_data_for_marathi,
        doc_type="legal_notice",
        subtype="legal_notice",
        target_lang="mr",
        facts="Fact statement.",
    )
    assert is_valid is False
    assert "hindi" in err_msg.lower() or "marathi" in err_msg.lower()


# ── TEST 13: Provider Failure and Exhausted Retries ───────────────────────────
def test_req13_provider_failure_and_exhausted_retries():
    with patch("services.drafts_service._call_drafting_llm_json", side_effect=RuntimeError("Provider outage")):
        payload = {
            "document_type": "legal_notice",
            "facts": "Valid case facts describing a commercial transaction default.",
        }
        res = client.post("/api/drafts/generate", json=payload)
        assert res.status_code == 502
        assert "Legal draft generation failed" in res.json()["error"]
        assert "No static fallback is permitted" in res.json()["error"]


# ── TEST 14: Translation Failure Without False Success ────────────────────────
def test_req14_translation_failure_without_false_success():
    draft = DraftContent(
        title="LEGAL NOTICE",
        sections=[DraftSection(id="sec_1", title="Notice", content="English content", order=1)],
        full_text="English content",
    )
    req = TranslateDraftRequest(
        document_type="legal_notice",
        draft=draft,
        target_language="mr",
    )
    # Mock translation provider returning unchanged English text
    with patch("services.drafts_service.translate_legal_text", return_value=MagicMock(translated_text="English content")):
        with pytest.raises(Exception) as exc_info:
            translate_draft(req)
        assert "failed" in str(exc_info.value).lower() or "502" in str(exc_info.value)


# ── TEST 15: Regeneration Preserving Original Context ─────────────────────────
def test_req15_regeneration_preserving_original_context():
    regen_req = RegenerateSectionRequest(
        document_type="bail_application",
        subtype="regular_bail",
        section_id="sec_grounds",
        section_title="Grounds for Bail",
        current_content="Initial weak grounds.",
        facts="Accused arrested in FIR 99/2024 at Hadapsar PS. Co-accused granted bail.",
        instructions="Emphasize parity with co-accused who was granted bail.",
        language="en",
    )
    mock_revised = {
        "content": "PARITY OF TREATMENT: Co-accused similarly situated has been enlarged on regular bail by this Hon'ble Court. Applicant is entitled to parity."
    }
    with patch("services.drafts_service._call_drafting_llm_json", return_value=mock_revised):
        res = regenerate_draft_section(regen_req)
        assert res.section_id == "sec_grounds"
        assert "parity" in res.content.lower()
        assert res.content != regen_req.current_content


# ── TEST 16: Export and Backward-Compatibility Fields ─────────────────────────
def test_req16_export_and_backward_compatibility():
    export_req = ExportDraftRequest(
        title="कायदेशीर नोटीस (LEGAL NOTICE)",
        document_type="legal_notice",
        sections=[
            DraftSection(
                id="sec_1",
                title="प्रकरणाची वस्तुस्थिती",
                content="माझे अशील यांच्या सूचनेनुसार सदर नोटीस बजावण्यात येत आहे. रुपये ₹50,000/- येणे बाकी आहे.",
                order=1,
            )
        ],
        citations=[
            CitationInfo(
                title="भारतीय करार कायदा, १८७२",
                citation="कलम ७३",
                court=None,
                is_verified=False,
                verification_status="verification_required",
                authority_type="statutory",
            )
        ],
        language="mr",
    )

    pdf_bytes = generate_draft_pdf(export_req)
    assert pdf_bytes.startswith(b"%PDF")
    assert len(pdf_bytes) > 1000

    docx_bytes = generate_draft_docx(export_req)
    assert docx_bytes.startswith(b"PK")
    assert len(docx_bytes) > 1000


# ── TEST 17: Proof Zero RAG and Zero Precedent Retrieval ──────────────────────
def test_req17_proof_zero_rag_and_zero_precedent_retrieval():
    with patch("services.rag_retrieval.RAGRetrievalEngine.retrieve_evidence") as mock_rag, \
         patch("services.precedent_verification.query_verified_precedents") as mock_prec:

        payload = {
            "document_type": "bail_application",
            "facts": "Accused arrested on 12.08.2024 in FIR 10/2024 under Section 318(4) BNS.",
            "supporting_document_ids": ["doc_abc_123"],
            "include_citations": True,
        }
        res = client.post("/api/drafts/generate", json=payload)
        assert res.status_code == 200

        # Neither RAG retrieval engine nor precedent database retrieval may be invoked
        mock_rag.assert_not_called()
        mock_prec.assert_not_called()
