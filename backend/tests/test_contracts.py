"""
Integration and Unit Test Suite for Feature 3.7: Contract Red-Flag Analyzer
NyayaSarathi Legal Intelligence Application
Tests cover:
1. Valid digital PDF ingestion and clause extraction
2. Valid DOCX ingestion and table/paragraph extraction
3. Scanned PDF with OCR availability
4. Scanned PDF when OCR is unavailable
5. Corrupted / malformed PDF handling
6. Unsupported file extension rejection (415)
7. Empty file rejection (400)
8. Oversized file rejection (413)
9. Encrypted / password-protected PDF handling
10. PDF parser error safety (no raw binary decoding)
11. LLM provider timeout / graceful heuristic fallback
12. Malformed LLM response recovery
13. Risk severity normalization and impact calibration
14. Clause grounding verification and unsupported quote omission
15. Exact page reference resolution
16. JWT Authentication and access control enforcement (401 vs 200)
17. Temporary file lifecycle cleanup
18. Existing public API schema backward compatibility
19. Realistic sample contract multi-clause coverage & High Risk classification
20. Renewal clause grounding (excludes introductory text)
21. Indemnity clause grounding (excludes liability cap text)
"""

import io
import os
import unittest
from unittest.mock import patch, MagicMock

import pymupdf as fitz
import docx
from fastapi.testclient import TestClient

from main import app
from schemas.contracts import ContractAnalysisResponse, RedFlag
from services.contracts_service import (
    extract_contract_text,
    analyze_contract,
    _verify_clause_grounding,
    _find_page_ref,
    _calibrate_clause_risk,
    _extract_operative_clause,
    MAX_FILE_SIZE_BYTES,
)
from services.user_repository import create_user, get_user_by_email
from services.auth_service import create_access_token


class TestContractRedFlagAnalyzer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.test_email = "contract_tester_qa@nyayasarathi.in"
        existing = get_user_by_email(cls.test_email)
        if not existing:
            cls.test_user = create_user(
                email=cls.test_email,
                full_name="Contract Legal Tester",
                role="USER",
                password_hash="dummy_hash",
            )
        else:
            cls.test_user = existing

        cls.token = create_access_token(
            user_id=cls.test_user["id"],
            email=cls.test_email,
            role=cls.test_user.get("role", "USER"),
        )
        cls.auth_headers = {"Authorization": f"Bearer {cls.token}"}

    def _create_sample_pdf(self, text: str = "This is a standard contract clause with unlimited liability.") -> bytes:
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((50, 72), text)
        page2 = doc.new_page()
        page2.insert_text((50, 72), "Second page contains an automatic renewal clause without prior notice.")
        pdf_bytes = doc.tobytes()
        doc.close()
        return pdf_bytes

    def _create_realistic_sample_pdf(self) -> bytes:
        """
        Creates a realistic 2-page commercial agreement containing multiple distinct,
        serious legal risks (renewal, non-compete, indemnity, liability cap, unilateral amendment,
        liquidated damages, and unilateral arbitrator).
        """
        doc = fitz.open()

        # Page 1: Scope, Term & Renewal, Restrictive Covenants
        p1 = doc.new_page()
        p1_text = (
            "COMMERCIAL SERVICES AGREEMENT\n\n"
            "Section 1. Scope of Services.\n"
            "The Service Provider shall provide technology consulting services to the Client as described in Schedule A.\n\n"
            "Section 2. Term and Duration.\n"
            "This Agreement commences on January 1, 2025 and shall continue in force for twelve months. "
            "Neither party may terminate early except as provided herein. "
            "Upon expiration of the Initial Term, this Agreement shall automatically renew for successive terms of "
            "twelve (12) months each, unless either party provides written notice of non-renewal at least ninety (90) days "
            "prior to the expiration of the then-current term.\n\n"
            "Section 3. Restraint of Trade.\n"
            "The Consultant covenants that for a period of twenty-four (24) months following termination of this Agreement for any reason, "
            "the Consultant shall not directly or indirectly engage in any business competing with the Company."
        )
        p1.insert_textbox(fitz.Rect(50, 50, 550, 750), p1_text)

        # Page 2: Liability, Indemnification, Amendments, Penalties, Dispute Resolution
        p2 = doc.new_page()
        p2_text = (
            "Section 4. Limitation of Liability and Indemnification.\n"
            "To the maximum extent permitted by applicable law, in no event shall Vendor's total aggregate liability under this "
            "Agreement exceed the fees paid in the preceding three months. "
            "Customer agrees to unconditionally indemnify, defend, and hold harmless Vendor, its officers, and affiliates from "
            "and against any and all claims, liabilities, losses, damages, costs, and expenses without limitation.\n\n"
            "Section 5. Unilateral Amendment.\n"
            "The Company reserves the right to modify, amend, or alter any terms, conditions, or pricing under this Agreement "
            "at any time in its sole discretion without prior notice.\n\n"
            "Section 6. Early Termination Penalties.\n"
            "If Client terminates this Agreement prior to the expiration of the term, Client shall immediately pay as "
            "liquidated damages a sum equal to 100% of the remaining contract value.\n\n"
            "Section 7. Dispute Resolution.\n"
            "All disputes shall be referred to arbitration before a sole arbitrator appointed exclusively by the Vendor, "
            "and the courts of New Delhi shall have exclusive jurisdiction."
        )
        p2.insert_textbox(fitz.Rect(50, 50, 550, 750), p2_text)

        pdf_bytes = doc.tobytes()
        doc.close()
        return pdf_bytes

    def _create_sample_docx(self, text: str = "This agreement contains a non-compete restraint of trade.") -> bytes:
        d = docx.Document()
        d.add_paragraph(text)
        d.add_paragraph("Either party may terminate for convenience with 30 days notice.")
        buf = io.BytesIO()
        d.save(buf)
        return buf.getvalue()

    # ── Test 1: Valid Digital PDF ─────────────────────────────────────────────
    def test_01_valid_digital_pdf(self):
        pdf_bytes = self._create_sample_pdf()
        ext_res = extract_contract_text("sample_agreement.pdf", "application/pdf", pdf_bytes)
        self.assertEqual(ext_res["extraction_method"], "digital_pdf")
        self.assertEqual(ext_res["total_pages"], 2)
        self.assertIn("unlimited liability", ext_res["text"].lower())
        self.assertEqual(len(ext_res["pages_data"]), 2)
        self.assertEqual(ext_res["pages_data"][0]["page_number"], 1)
        self.assertEqual(ext_res["pages_data"][1]["page_number"], 2)

    # ── Test 2: Valid DOCX ────────────────────────────────────────────────────
    def test_02_valid_docx(self):
        docx_bytes = self._create_sample_docx()
        ext_res = extract_contract_text("vendor_agreement.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", docx_bytes)
        self.assertEqual(ext_res["extraction_method"], "docx")
        self.assertIn("non-compete", ext_res["text"].lower())
        # Page numbers for DOCX should be None
        self.assertIsNone(ext_res["pages_data"][0]["page_number"])

    # ── Test 3: Scanned PDF with OCR Available ────────────────────────────────
    @patch("services.ocr.pdf_extractor.PDFExtractor.extract_text")
    def test_03_scanned_pdf_with_ocr_available(self, mock_ocr_extract):
        doc = fitz.open()
        page = doc.new_page()
        img_pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 50, 50), 1)
        page.insert_image(page.rect, pixmap=img_pix)
        scanned_bytes = doc.tobytes()
        doc.close()

        mock_ocr_extract.return_value = [{
            "page_number": 1,
            "text": "Scanned contract text with indemnification obligations extracted via PaddleOCR.",
            "confidence": 0.94,
            "blocks": [],
        }]

        ext_res = extract_contract_text("scanned_order.pdf", "application/pdf", scanned_bytes)
        self.assertIn("indemnification", ext_res["text"].lower())
        self.assertIn("scanned", ext_res["extraction_method"])

    # ── Test 4: Scanned PDF when OCR is Unavailable ───────────────────────────
    @patch("services.ocr.pdf_extractor.PDFExtractor.extract_text", side_effect=RuntimeError("PaddleOCR not loaded"))
    def test_04_scanned_pdf_when_ocr_unavailable(self, mock_ocr_extract):
        doc = fitz.open()
        page = doc.new_page()
        img_pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 50, 50), 1)
        page.insert_image(page.rect, pixmap=img_pix)
        page.insert_text((50, 50), "Some minor text but mostly scanned")
        pdf_bytes = doc.tobytes()
        doc.close()

        ext_res = extract_contract_text("scanned_fallback.pdf", "application/pdf", pdf_bytes)
        self.assertIn("warnings", ext_res)
        self.assertTrue(len(ext_res["warnings"]) > 0)

    # ── Test 5: Invalid / Malformed PDF ───────────────────────────────────────
    def test_05_invalid_or_malformed_pdf(self):
        malformed_bytes = b"This is not a real PDF file header"
        with self.assertRaises(ValueError) as ctx:
            extract_contract_text("corrupt.pdf", "application/pdf", malformed_bytes)
        self.assertIn("Invalid PDF file", str(ctx.exception))

    # ── Test 6: Unsupported Extension ─────────────────────────────────────────
    def test_06_unsupported_extension(self):
        res = self.client.post(
            "/api/contracts/analyze",
            files={"file": ("malicious.exe", b"MZexecutable", "application/x-msdownload")},
            headers=self.auth_headers,
        )
        self.assertEqual(res.status_code, 415)
        err_msg = res.json().get("error") or res.json().get("detail", "")
        self.assertIn("Unsupported file format", err_msg)

    # ── Test 7: Empty Document ────────────────────────────────────────────────
    def test_07_empty_document(self):
        res = self.client.post(
            "/api/contracts/analyze",
            files={"file": ("empty.pdf", b"", "application/pdf")},
            headers=self.auth_headers,
        )
        self.assertEqual(res.status_code, 400)
        err_msg = res.json().get("error") or res.json().get("detail", "")
        self.assertIn("empty", err_msg.lower())

    # ── Test 8: Oversized Upload ──────────────────────────────────────────────
    def test_08_oversized_upload(self):
        oversized_bytes = b"%PDF" + (b"0" * (MAX_FILE_SIZE_BYTES + 1024))
        res = self.client.post(
            "/api/contracts/analyze",
            files={"file": ("huge.pdf", oversized_bytes, "application/pdf")},
            headers=self.auth_headers,
        )
        self.assertEqual(res.status_code, 413)

    # ── Test 9: Encrypted PDF ─────────────────────────────────────────────────
    def test_09_encrypted_pdf(self):
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((50, 72), "Confidential locked agreement")
        encrypted_bytes = doc.tobytes(encryption=fitz.PDF_ENCRYPT_AES_256, user_pw="secret123")
        doc.close()

        with self.assertRaises(ValueError) as ctx:
            extract_contract_text("locked.pdf", "application/pdf", encrypted_bytes)
        self.assertIn("encrypted", str(ctx.exception).lower())

    # ── Test 10: PDF Extraction Failure Handling ──────────────────────────────
    def test_10_pdf_extraction_failure(self):
        broken_bytes = b"%PDF-1.4 garbage binary stream that causes parser failure"
        with self.assertRaises(ValueError) as ctx:
            extract_contract_text("broken.pdf", "application/pdf", broken_bytes)
        self.assertTrue("parse" in str(ctx.exception).lower() or "unreadable" in str(ctx.exception).lower())

    # ── Test 11: LLM Provider Timeout / Failure Fallback ──────────────────────
    @patch("services.contracts_service._call_contract_llm", return_value=(None, "error", "Timeout"))
    def test_11_llm_provider_timeout_fallback(self, mock_llm):
        pdf_bytes = self._create_sample_pdf("Clause: The Contractor shall have unlimited liability for all direct and indirect damages.")
        res = analyze_contract("service_agreement.pdf", "application/pdf", pdf_bytes)
        self.assertIsInstance(res, ContractAnalysisResponse)
        self.assertTrue(len(res.red_flags) > 0)
        self.assertEqual(res.overall_risk_score, "High")
        self.assertIn("unlimited liability", res.red_flags[0].clause_text.lower())

    # ── Test 12: Malformed LLM Response Recovery ──────────────────────────────
    @patch("services.contracts_service._call_contract_llm", return_value=({"invalid_key": "bad_schema"}, "groq", "llama"))
    def test_12_malformed_llm_response(self, mock_llm):
        pdf_bytes = self._create_sample_pdf("The Supplier may unilaterally modify pricing with immediate effect.")
        res = analyze_contract("pricing.pdf", "application/pdf", pdf_bytes)
        self.assertIsInstance(res, ContractAnalysisResponse)
        self.assertTrue(len(res.red_flags) > 0)
        categories = [f.risk_category.lower() for f in res.red_flags if f.risk_category]
        self.assertTrue(any("unilateral" in cat for cat in categories))

    # ── Test 13: Invalid Risk Severity Normalization & Impact Calibration ─────
    @patch("services.contracts_service._call_contract_llm")
    def test_13_invalid_risk_severity_calibrated(self, mock_llm):
        mock_llm.return_value = ({
            "summary": "Sample test contract",
            "overall_risk_score": "EXTREME",
            "red_flags": [
                {
                    "clause_text": "The Contractor shall have unlimited liability.",
                    "risk_level": "CRITICAL_DANGER",  # Non-standard
                    "risk_category": "liability",
                    "explanation": "Uncapped exposure.",
                    "recommendation": "Cap liability.",
                    "page_ref": 1,
                    "confidence": 0.95,
                }
            ],
            "limitations": []
        }, "groq", "llama")

        pdf_bytes = self._create_sample_pdf("The Contractor shall have unlimited liability.")
        res = analyze_contract("liability.pdf", "application/pdf", pdf_bytes)
        # Calibrated based on actual legal impact ("unlimited liability" -> high)
        self.assertEqual(res.red_flags[0].risk_level, "high")
        self.assertEqual(res.overall_risk_score, "High")

    # ── Test 14: Clause Grounding Verification & Unsupported Quote Omission ───
    def test_14_clause_grounding_verification(self):
        doc_text = "The Customer agrees to indemnify the Company against all third-party claims."
        # Verbatim clause should have high confidence
        is_grounded, conf, exact_span = _verify_clause_grounding("indemnify the Company against all third-party claims", doc_text)
        self.assertTrue(is_grounded)
        self.assertGreaterEqual(conf, 0.85)

        # Hallucinated clause should be flagged False
        is_untrue, conf_low, _ = _verify_clause_grounding("The supplier forfeits all intellectual property patents across the galaxy", doc_text)
        self.assertFalse(is_untrue)
        self.assertLess(conf_low, 0.50)

    # ── Test 15: Correct Page References ──────────────────────────────────────
    def test_15_correct_page_references(self):
        pages_data = [
            {"page_number": 1, "text": "Preliminary clauses and recital."},
            {"page_number": 2, "text": "Clause 14: Non-compete restraint of trade."},
        ]
        p_ref = _find_page_ref("Non-compete restraint", pages_data)
        self.assertEqual(p_ref, 2)

    # ── Test 16: Authentication and Access Control ────────────────────────────
    def test_16_authentication_enforcement(self):
        pdf_bytes = self._create_sample_pdf()
        # 1. Unauthenticated request returns 401
        unauth_res = self.client.post(
            "/api/contracts/analyze",
            files={"file": ("contract.pdf", pdf_bytes, "application/pdf")},
        )
        self.assertEqual(unauth_res.status_code, 401)
        err_msg = unauth_res.json().get("error") or unauth_res.json().get("detail", "")
        self.assertIn("Authentication token is missing", err_msg)

        # 2. Authenticated request succeeds with 200
        auth_res = self.client.post(
            "/api/contracts/analyze",
            files={"file": ("contract.pdf", pdf_bytes, "application/pdf")},
            headers=self.auth_headers,
        )
        self.assertEqual(auth_res.status_code, 200)
        data = auth_res.json()
        self.assertIn("overall_risk_score", data)
        self.assertIn("red_flags", data)

    # ── Test 17: Safe Cleanup of Temporary Files ──────────────────────────────
    @patch("services.ocr.pdf_extractor.PDFExtractor.extract_text")
    def test_17_cleanup_after_extraction(self, mock_ocr):
        import tempfile
        doc = fitz.open()
        page = doc.new_page()
        page.insert_image(page.rect, pixmap=fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 50, 50), 1))
        pdf_bytes = doc.tobytes()
        doc.close()

        mock_ocr.return_value = [{"page_number": 1, "text": "OCR text", "confidence": 0.9}]
        temp_dir_before = set(os.listdir(tempfile.gettempdir()))

        extract_contract_text("temp_test.pdf", "application/pdf", pdf_bytes)

        temp_dir_after = set(os.listdir(tempfile.gettempdir()))
        new_pdf_files = [f for f in (temp_dir_after - temp_dir_before) if f.endswith(".pdf")]
        self.assertEqual(len(new_pdf_files), 0)

    # ── Test 18: Existing API Response Compatibility ──────────────────────────
    def test_18_existing_api_response_compatibility(self):
        pdf_bytes = self._create_sample_pdf()
        res = self.client.post(
            "/api/contracts/analyze",
            files={"file": ("sample.pdf", pdf_bytes, "application/pdf")},
            headers=self.auth_headers,
        )
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertIn("overall_risk_score", body)
        self.assertIn("red_flags", body)
        self.assertIsInstance(body["red_flags"], list)
        self.assertTrue(len(body["red_flags"]) > 0)
        rf0 = body["red_flags"][0]
        self.assertIn("clause_text", rf0)
        self.assertIn("risk_level", rf0)
        self.assertIn("explanation", rf0)
        self.assertIn("page_ref", rf0)

    # ── Test 19: Realistic Sample PDF Multi-Clause Coverage & High Risk ───────
    def test_19_realistic_sample_pdf_coverage_and_high_risk(self):
        """
        Verifies that a realistic contract with multiple serious clauses produces:
        - Overall risk score: High
        - Multiple High Risk findings (not zero)
        - Broad coverage of distinct clauses (at least 4 distinct risk findings)
        """
        pdf_bytes = self._create_realistic_sample_pdf()
        res = analyze_contract("commercial_agreement.pdf", "application/pdf", pdf_bytes)

        self.assertEqual(res.overall_risk_score, "High")
        self.assertGreaterEqual(res.risk_counts["high"], 2, "Expected multiple high risk findings")
        self.assertGreaterEqual(len(res.red_flags), 4, "Expected broad coverage across distinct provisions")

        categories = {f.risk_category for f in res.red_flags}
        self.assertTrue(
            categories.intersection({"indemnity", "liability", "restrictive_covenants", "renewal_lockin", "unilateral_modification"}),
            "Expected key contractual risk categories to be identified"
        )

    # ── Test 20: Renewal Finding Quotes Clause, Not Introductory Header ───────
    def test_20_renewal_finding_grounds_actual_clause(self):
        """
        Verifies that the automatic renewal finding quotes the actual operative clause:
        'Upon expiration of the Initial Term, this Agreement shall automatically renew...'
        and NOT the introductory text:
        'Section 2. Term and Duration. This Agreement commences...'
        """
        pdf_bytes = self._create_realistic_sample_pdf()
        res = analyze_contract("commercial_agreement.pdf", "application/pdf", pdf_bytes)

        renewal_flags = [f for f in res.red_flags if f.risk_category == "renewal_lockin"]
        self.assertTrue(len(renewal_flags) > 0, "Expected a renewal finding")

        renewal_clause = renewal_flags[0].clause_text
        self.assertIn("automatically renew", renewal_clause.lower())
        self.assertFalse(
            renewal_clause.lower().startswith("section 2"),
            f"Renewal finding should not quote introductory section title. Found: {renewal_clause}"
        )
        self.assertFalse(
            "this agreement commences on january 1, 2025" in renewal_clause.lower() and "automatically renew" not in renewal_clause.lower(),
            "Renewal finding should not quote initial duration without renewal terms"
        )
        self.assertEqual(renewal_flags[0].page_ref, 1, "Renewal clause appears on page 1")

    # ── Test 21: Indemnity Finding Quotes Indemnity, Not Liability Cap ────────
    def test_21_indemnity_finding_grounds_actual_clause(self):
        """
        Verifies that the indemnity finding quotes:
        'Customer agrees to unconditionally indemnify, defend, and hold harmless...'
        and NOT the liability cap:
        'in no event shall Vendor's total aggregate liability...'
        """
        pdf_bytes = self._create_realistic_sample_pdf()
        res = analyze_contract("commercial_agreement.pdf", "application/pdf", pdf_bytes)

        indemnity_flags = [f for f in res.red_flags if f.risk_category == "indemnity"]
        self.assertTrue(len(indemnity_flags) > 0, "Expected an indemnity finding")

        indemnity_clause = indemnity_flags[0].clause_text
        self.assertIn("indemnif", indemnity_clause.lower())
        self.assertNotIn(
            "in no event shall vendor's total aggregate liability",
            indemnity_clause.lower(),
            f"Indemnity finding should not quote liability cap. Found: {indemnity_clause}"
        )
        self.assertEqual(indemnity_flags[0].page_ref, 2, "Indemnity clause appears on page 2")
        self.assertEqual(indemnity_flags[0].risk_level, "high", "Unconditional uncapped indemnity must be High Risk")

    # ── Test 22: Hallucinated / Unsupported LLM Quotes Are Omitted ───────────
    @patch("services.contracts_service._call_contract_llm")
    def test_22_unsupported_llm_quotes_are_omitted(self, mock_llm):
        """
        Verifies that when an LLM returns an unsupported/hallucinated quote not present in the contract,
        it is omitted from verified findings and recorded in limitations.
        """
        pdf_bytes = self._create_realistic_sample_pdf()
        mock_llm.return_value = ({
            "summary": "AI summary of contract",
            "overall_risk_score": "High",
            "red_flags": [
                {
                    # Grounded clause present in PDF
                    "clause_text": "Customer agrees to unconditionally indemnify, defend, and hold harmless Vendor",
                    "risk_level": "high",
                    "risk_category": "indemnity",
                    "explanation": "Uncapped indemnity.",
                    "recommendation": "Cap indemnity.",
                    "page_ref": 2,
                    "confidence": 0.95,
                },
                {
                    # Fabricated clause NOT present in PDF
                    "clause_text": "The Client hereby assigns all copyrights in the Solar System to Vendor forever.",
                    "risk_level": "high",
                    "risk_category": "confidentiality_ip",
                    "explanation": "Fabricated clause.",
                    "recommendation": "Delete.",
                    "page_ref": 1,
                    "confidence": 0.90,
                }
            ],
            "limitations": []
        }, "groq", "llama")

        res = analyze_contract("test.pdf", "application/pdf", pdf_bytes)
        reported_texts = [f.clause_text for f in res.red_flags]

        # Grounded clause is retained
        self.assertTrue(any("indemnif" in t.lower() for t in reported_texts))
        # Fabricated clause is strictly omitted!
        self.assertFalse(any("solar system" in t.lower() for t in reported_texts))
        # Limitation was recorded
        self.assertTrue(any("omitted" in lim.lower() for lim in res.limitations))


if __name__ == "__main__":
    unittest.main()
