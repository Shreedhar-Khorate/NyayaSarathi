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
    classify_document,
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

    def _create_court_judgment_pdf(self) -> bytes:
        """
        Creates a synthetic court judgment PDF mirroring the Bombay High Court
        interim maintenance judgment (Roma Rajesh Tiwari vs Rajesh Dinanath Tiwari).
        """
        doc = fitz.open()
        p1 = doc.new_page()
        p1_text = (
            "IN THE HIGH COURT OF JUDICATURE AT BOMBAY\n"
            "CIVIL APPELLATE JURISDICTION\n"
            "WRIT PETITION NO. 10187 OF 2017\n\n"
            "Roma Rajesh Tiwari ... Petitioner\n"
            "versus\n"
            "Rajesh Dinanath Tiwari ... Respondent\n\n"
            "CORAM: SMT. BHARATI H. DANGRE, J.\n"
            "DATED: 12TH OCTOBER, 2017\n\n"
            "ORAL JUDGMENT:\n"
            "1. Rule. Rule is made returnable forthwith and heard finally by consent of parties.\n"
            "2. The challenge in the present Writ Petition is to the order passed by the Judge, "
            "Family Court No. 3, Mumbai below Exhibit 13 in Petition No. A-1498 of 2015 on 18th July 2017. "
            "By the impugned order, the application filed by the Petitioner-wife under Section 24 of the "
            "Hindu Marriage Act, 1955 seeking interim maintenance came to be rejected.\n"
            "3. Heard the learned counsel for the petitioner and the respondent.\n"
            "4. The operative order grants interim maintenance of Rs. 20,000 per month. Petition is allowed."
        )
        p1.insert_textbox(fitz.Rect(50, 50, 550, 750), p1_text)
        pdf_bytes = doc.tobytes()
        doc.close()
        return pdf_bytes

    def _create_legal_notice_pdf(self) -> bytes:
        """
        Creates a synthetic formal legal notice / demand notice PDF.
        """
        doc = fitz.open()
        p1 = doc.new_page()
        p1_text = (
            "LEGAL NOTICE / STATUTORY DEMAND UNDER SECTION 138 NEGOTIABLE INSTRUMENTS ACT\n\n"
            "To: ABC Infotech Private Limited\n"
            "From: Adv. S. Sharma, High Court of Bombay\n\n"
            "Sir/Madam,\n"
            "Under instructions from my client, I hereby call upon you to remit the outstanding "
            "statutory sum of Rs. 15,00,000 within 15 days of receipt of this legal notice, "
            "failing which my client shall initiate criminal prosecution under Section 138 of the NI Act."
        )
        p1.insert_textbox(fitz.Rect(50, 50, 550, 750), p1_text)
        pdf_bytes = doc.tobytes()
        doc.close()
        return pdf_bytes

    def _create_balanced_safe_contract_pdf(self) -> bytes:
        """
        Creates a balanced, mutual commercial contract without unreciprocal or high-risk red flags.
        """
        doc = fitz.open()
        p1 = doc.new_page()
        p1_text = (
            "COMMERCIAL SERVICES AGREEMENT\n\n"
            "This Agreement is made and entered into by and between Alpha Solutions Ltd and Beta Corp.\n"
            "WHEREAS both parties wish to collaborate on software development support services.\n"
            "NOW THEREFORE, the parties hereby agree as follows:\n\n"
            "Section 1. Scope of Work.\n"
            "Provider will deliver quarterly consulting deliverables as described in Statement of Work.\n\n"
            "Section 2. Term and Mutual Renewal.\n"
            "This Agreement continues for 12 months. Any renewal requires mutual written confirmation signed by both parties.\n\n"
            "Section 3. Balanced Termination.\n"
            "Either party may terminate this agreement upon sixty (60) days prior written notice.\n\n"
            "Section 4. Mutual Limitation of Liability.\n"
            "Each party's aggregate liability under this agreement shall be capped at fees paid in the preceding 12 months.\n\n"
            "IN WITNESS WHEREOF, the parties hereto have executed this Agreement."
        )
        p1.insert_textbox(fitz.Rect(50, 50, 550, 750), p1_text)
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
    @patch("services.contracts_service._call_contract_llm", return_value=(None, "none", "mock"))
    def test_16_authentication_enforcement(self, mock_llm):
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
    @patch("services.contracts_service._call_contract_llm", return_value=(None, "none", "mock"))
    def test_18_existing_api_response_compatibility(self, mock_llm):
        pdf_bytes = self._create_sample_pdf()
        res = self.client.post(
            "/api/contracts/analyze",
            files={"file": ("sample_agreement.pdf", pdf_bytes, "application/pdf")},
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
    @patch("services.contracts_service._call_contract_llm", return_value=(None, "none", "mock"))
    def test_19_realistic_sample_pdf_coverage_and_high_risk(self, mock_llm):
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
    @patch("services.contracts_service._call_contract_llm", return_value=(None, "none", "mock"))
    def test_20_renewal_finding_grounds_actual_clause(self, mock_llm):
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
    @patch("services.contracts_service._call_contract_llm", return_value=(None, "none", "mock"))
    def test_21_indemnity_finding_grounds_actual_clause(self, mock_llm):
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

        res = analyze_contract("test_agreement.pdf", "application/pdf", pdf_bytes)
        reported_texts = [f.clause_text for f in res.red_flags]

        # Grounded clause is retained
        self.assertTrue(any("indemnif" in t.lower() for t in reported_texts))
        # Fabricated clause is strictly omitted!
        self.assertFalse(any("solar system" in t.lower() for t in reported_texts))
        # Limitation was recorded
        self.assertTrue(any("omitted" in lim.lower() for lim in res.limitations))

    # ── Test 23: Court Judgment Uploaded as Contract Returns Mismatch ────────
    def test_23_court_judgment_uploaded_as_contract_returns_mismatch(self):
        """
        Scenario 1: Court judgment uploaded as a contract.
        - Must be classified as court_judgment
        - audit_status == DOCUMENT_TYPE_MISMATCH
        - overall_risk_score == "Not Assessed" (never Low Risk)
        - red_flags == []
        - risk_counts == all 0
        - Executive summary explains document mismatch
        - recommended_action points to Legal Research / Case Predictor
        """
        pdf_bytes = self._create_court_judgment_pdf()
        res = analyze_contract(
            "Roma_Rajesh_Tiwari_vs_Rajesh_Dinanath_Tiwari_on_12_October_2017.PDF",
            "application/pdf",
            pdf_bytes,
        )

        self.assertEqual(res.document_type, "court_judgment")
        self.assertEqual(res.document_type_label, "Court Judgment / Judicial Order")
        self.assertEqual(res.audit_status, "DOCUMENT_TYPE_MISMATCH")
        self.assertEqual(res.overall_risk_score, "Not Assessed")
        self.assertEqual(len(res.red_flags), 0, "No contract red flags should be extracted from court judgments")
        self.assertEqual(res.risk_counts["high"], 0)
        self.assertEqual(res.risk_counts["medium"], 0)
        self.assertEqual(res.risk_counts["low"], 0)
        self.assertEqual(res.risk_counts["total"], 0)

        # Executive summary must explain mismatch and never claim Low Risk
        self.assertIn("Court Judgment / Judicial Order", res.summary)
        self.assertIn("not applicable", res.summary.lower())
        self.assertNotIn("low risk", res.summary.lower())

        # Recommendations guide user to appropriate modules
        self.assertTrue(
            "Legal Research" in res.recommended_action or "Case Predictor" in res.recommended_action
        )

    # ── Test 24: Court Judgment via API Endpoint & Activity Logging ───────────
    def test_24_court_judgment_api_endpoint_and_activity_logging(self):
        """
        Scenario 11: Activity history & API endpoint verification.
        - POST /api/contracts/analyze with judgment returns 200 with DOCUMENT_TYPE_MISMATCH
        - Logged user activity records Document Mismatch with Not Assessed risk
        - Never logged as 'Low Risk'
        """
        pdf_bytes = self._create_court_judgment_pdf()
        filename = "Roma_Rajesh_Tiwari_vs_Rajesh_Dinanath_Tiwari.pdf"

        res = self.client.post(
            "/api/contracts/analyze",
            files={"file": (filename, pdf_bytes, "application/pdf")},
            headers=self.auth_headers,
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()

        self.assertEqual(data["audit_status"], "DOCUMENT_TYPE_MISMATCH")
        self.assertEqual(data["overall_risk_score"], "Not Assessed")
        self.assertEqual(data["document_type"], "court_judgment")
        self.assertEqual(len(data["red_flags"]), 0)

        # Verify activity history in database
        from services.user_repository import get_db_connection
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT title, query_text, metadata FROM user_activity_history WHERE user_id = ? ORDER BY created_at DESC LIMIT 1",
                (self.test_user["id"],),
            )
            row = cursor.fetchone()
            self.assertIsNotNone(row, "User activity must be recorded")
            title = row["title"] if isinstance(row, dict) else row[0]
            query_text = row["query_text"] if isinstance(row, dict) else row[1]
            self.assertIn("Document Mismatch", title)
            self.assertNotIn("Low Risk", title)
            self.assertIn("Not Assessed", query_text)

    # ── Test 25: Legal Notice Mismatch ────────────────────────────────────────
    def test_25_legal_notice_mismatch(self):
        """
        Verifies that a formal legal demand notice is correctly classified as
        DOCUMENT_TYPE_MISMATCH with document_type: legal_notice.
        """
        pdf_bytes = self._create_legal_notice_pdf()
        res = analyze_contract("legal_notice_section_138.pdf", "application/pdf", pdf_bytes)

        self.assertEqual(res.document_type, "legal_notice")
        self.assertEqual(res.audit_status, "DOCUMENT_TYPE_MISMATCH")
        self.assertEqual(res.overall_risk_score, "Not Assessed")
        self.assertEqual(len(res.red_flags), 0)

    # ── Test 26: Valid Commercial Contract with No Detected Red Flags ─────────
    @patch("services.contracts_service._call_contract_llm")
    def test_26_valid_commercial_contract_zero_red_flags(self, mock_llm):
        """
        Scenario 2: Valid commercial contract with no detected red flags.
        - audit_status == COMPLETED
        - overall_risk_score == Low
        - red_flags == []
        - Summary clarifies that zero detected flags does not guarantee absolute safety.
        """
        mock_llm.return_value = ({
            "summary": "Standard fair commercial agreement with balanced mutual obligations.",
            "overall_risk_score": "Low",
            "red_flags": [],
            "limitations": []
        }, "groq", "llama")

        pdf_bytes = self._create_balanced_safe_contract_pdf()
        res = analyze_contract("commercial_services_agreement.pdf", "application/pdf", pdf_bytes)

        self.assertEqual(res.audit_status, "COMPLETED")
        self.assertIn(res.document_type, ["commercial_contract", "executed_contract"])
        self.assertEqual(res.overall_risk_score, "Low")
        self.assertEqual(len(res.red_flags), 0)
        self.assertEqual(res.risk_counts["total"], 0)
        self.assertIn("No high-risk, unreciprocal, or statutory red flags were detected", res.summary)
        self.assertIn("does not guarantee complete legal suitability", res.summary)

    # ── Test 27: Explicit Unilateral Termination Clause ───────────────────────
    @patch("services.contracts_service._call_contract_llm", return_value=(None, "none", "mock"))
    def test_27_explicit_unilateral_termination_clause(self, mock_llm):
        """
        Scenario 3: Explicit unilateral termination clause.
        - Clause is cited verbatim
        - Severity is High
        - Categorized as termination
        """
        doc = fitz.open()
        p = doc.new_page()
        p.insert_text(
            (50, 72),
            "COMMERCIAL AGREEMENT\n\n"
            "Section 9. Termination.\n"
            "The Company reserves the right to terminate this agreement at any time immediately "
            "without cause and without prior notice at its sole discretion."
        )
        pdf_bytes = doc.tobytes()
        doc.close()

        res = analyze_contract("master_agreement.pdf", "application/pdf", pdf_bytes)
        term_flags = [f for f in res.red_flags if f.risk_category == "termination"]
        self.assertTrue(len(term_flags) > 0, "Expected unilateral termination finding")
        self.assertEqual(term_flags[0].risk_level, "high")
        self.assertIn("without cause", term_flags[0].clause_text.lower())

    # ── Test 28: Broad Indemnity Evidence Grounding ───────────────────────────
    @patch("services.contracts_service._call_contract_llm", return_value=(None, "none", "mock"))
    def test_28_broad_indemnity_evidence_grounding(self, mock_llm):
        """
        Scenario 4: Broad indemnity clause.
        - Evidence grounding verified
        - Distinguishes commercial exposure from invalidity
        """
        doc = fitz.open()
        p = doc.new_page()
        p.insert_text(
            (50, 72),
            "SERVICES AGREEMENT\n\n"
            "Section 8. Indemnification.\n"
            "The Customer agrees to unconditionally indemnify and hold harmless the Vendor from all third-party liabilities."
        )
        pdf_bytes = doc.tobytes()
        doc.close()

        res = analyze_contract("services_contract.pdf", "application/pdf", pdf_bytes)
        indem_flags = [f for f in res.red_flags if f.risk_category == "indemnity"]
        self.assertTrue(len(indem_flags) > 0)
        self.assertIn("indemnify and hold harmless", indem_flags[0].clause_text.lower())
        self.assertEqual(indem_flags[0].risk_level, "high")

    # ── Test 29: Post-Termination Non-Compete Section 27 Grounding ────────────
    @patch("services.contracts_service._call_contract_llm", return_value=(None, "none", "mock"))
    def test_29_post_termination_non_compete_section_27(self, mock_llm):
        """
        Scenario 5: Post-termination non-compete restraint of trade.
        - Cites Section 27 Indian Contract Act 1872
        - Categorized as restrictive_covenants with High Risk
        """
        doc = fitz.open()
        p = doc.new_page()
        p.insert_text(
            (50, 72),
            "EMPLOYMENT AGREEMENT\n\n"
            "Section 11. Restrictive Covenants.\n"
            "The Employee covenants not to compete or engage in any competing business for three years post-termination."
        )
        pdf_bytes = doc.tobytes()
        doc.close()

        res = analyze_contract("employment_agreement.pdf", "application/pdf", pdf_bytes)
        nc_flags = [f for f in res.red_flags if f.risk_category == "restrictive_covenants"]
        self.assertTrue(len(nc_flags) > 0)
        self.assertIn("Section 27", nc_flags[0].explanation)
        self.assertEqual(nc_flags[0].risk_level, "high")

    # ── Test 30: Insufficient Content Document Handling ───────────────────────
    def test_30_insufficient_content_returns_proper_status(self):
        """
        Scenario 6: Incomplete / minimal text returns INSUFFICIENT_CONTENT.
        - audit_status == INSUFFICIENT_CONTENT
        - overall_risk_score == 'Not Assessed' (never Low Risk)
        - red_flags == []
        """
        doc = fitz.open()
        p = doc.new_page()
        p.insert_text((50, 72), "Brief memo")
        pdf_bytes = doc.tobytes()
        doc.close()

        res = analyze_contract("memo.pdf", "application/pdf", pdf_bytes)
        self.assertEqual(res.audit_status, "INSUFFICIENT_CONTENT")
        self.assertEqual(res.overall_risk_score, "Not Assessed")
        self.assertEqual(len(res.red_flags), 0)

    # ── Test 31: Ambiguous or General Legal Document ──────────────────────────
    def test_31_ambiguous_or_general_legal_document(self):
        """
        Scenario 12: Mixed or ambiguous legal document without contractual covenants.
        - Handled explicitly as other_legal_document
        - audit_status == DOCUMENT_TYPE_MISMATCH
        - overall_risk_score == 'Not Assessed'
        """
        doc = fitz.open()
        p = doc.new_page()
        p.insert_text(
            (50, 72),
            "Historical treatise on jurisprudence and natural law in ancient societies. "
            "Legal philosophers have long debated the moral underpinnings of justice, equity, "
            "and civic virtue without addressing commercial contracts or reciprocal transactions."
        )
        pdf_bytes = doc.tobytes()
        doc.close()

        res = analyze_contract("philosophy_treatise.pdf", "application/pdf", pdf_bytes)
        self.assertEqual(res.document_type, "other_legal_document")
        self.assertEqual(res.audit_status, "DOCUMENT_TYPE_MISMATCH")
        self.assertEqual(res.overall_risk_score, "Not Assessed")
        self.assertEqual(len(res.red_flags), 0)

    # ── Test 32: Direct Unit Tests for Document Classifier ────────────────────
    def test_32_classify_document_unit_coverage(self):
        """
        Directly validates the document classification gate against all required types.
        """
        # 1. Court Judgment
        judg_res = classify_document(
            "IN THE HIGH COURT OF BOMBAY WRIT PETITION NO 100 OF 2020 PETITIONER VS RESPONDENT CORAM: HONBLE JUDGE ORAL JUDGMENT"
        )
        self.assertEqual(judg_res["document_type"], "court_judgment")
        self.assertFalse(judg_res["is_contract"])
        self.assertEqual(judg_res["audit_status"], "DOCUMENT_TYPE_MISMATCH")

        # 2. Legal Notice
        notice_res = classify_document(
            "LEGAL NOTICE UNDER INSTRUCTIONS FROM MY CLIENT I HEREBY CALL UPON YOU FAILING WHICH MY CLIENT SHALL INITIATE PROCEEDINGS"
        )
        self.assertEqual(notice_res["document_type"], "legal_notice")
        self.assertFalse(notice_res["is_contract"])

        # 3. Legal Opinion
        op_res = classify_document(
            "LEGAL OPINION AND MEMORANDUM OF LAW IN RE OPINION SOUGHT REGARDING REGULATORY COMPLIANCE OUR OPINION IS AS FOLLOWS"
        )
        self.assertEqual(op_res["document_type"], "legal_opinion")
        self.assertFalse(op_res["is_contract"])

        # 4. Non-Disclosure Agreement
        nda_res = classify_document(
            "MUTUAL NON-DISCLOSURE AGREEMENT THIS AGREEMENT IS ENTERED INTO BY AND BETWEEN THE PARTIES FOR CONFIDENTIALITY"
        )
        self.assertEqual(nda_res["document_type"], "nda")
        self.assertTrue(nda_res["is_contract"])
        self.assertEqual(nda_res["audit_status"], "COMPLETED")

        # 5. Employment Agreement
        emp_res = classify_document(
            "EMPLOYMENT AGREEMENT THIS AGREEMENT SETS FORTH TERMS OF EMPLOYMENT BETWEEN EMPLOYER AND EMPLOYEE"
        )
        self.assertEqual(emp_res["document_type"], "employment_agreement")
        self.assertTrue(emp_res["is_contract"])

        # 6. Lease Agreement
        lease_res = classify_document(
            "LEASE AGREEMENT AND RENTAL DEED THIS LEAVE AND LICENSE AGREEMENT BY AND BETWEEN LESSOR AND LESSEE"
        )
        self.assertEqual(lease_res["document_type"], "lease_agreement")
        self.assertTrue(lease_res["is_contract"])

        # 7. Service Agreement
        sla_res = classify_document(
            "MASTER SERVICES AGREEMENT THIS SLA IS EXECUTED BY AND BETWEEN CLIENT AND SERVICE PROVIDER"
        )
        self.assertEqual(sla_res["document_type"], "service_agreement")
        self.assertTrue(sla_res["is_contract"])

        # 8. Insufficient content
        short_res = classify_document("Too short")
        self.assertEqual(short_res["document_type"], "unknown")
        self.assertEqual(short_res["audit_status"], "INSUFFICIENT_CONTENT")
        self.assertFalse(short_res["is_contract"])

    # ── Test 33: Tender / RFP Classification & Procurement Risk Analysis ───────
    def test_33_tender_rfp_classification_and_procurement_risk(self):
        """
        Scenario: Public Tender / RFP with instructions to bidders, EMD, and procurement clauses.
        - Classified accurately as tender_rfp (not executed contract)
        - is_contract is True, audit_status is COMPLETED
        - Flags procurement discretionary terms and EMD forfeiture
        """
        tender_text = (
            "BUREAU OF INDIAN STANDARDS\n"
            "NOTICE INVITING TENDER (NIT) NO. BIS/IT/2025/01\n"
            "REQUEST FOR PROPOSAL (RFP) FOR ESTABLISHMENT OF MODERN RECORD ROOM\n\n"
            "Section 1. Instructions to Bidders (ITB).\n"
            "Earnest Money Deposit (EMD): The bidder shall furnish an EMD of INR 5,00,000. "
            "The bid security shall be forfeited if the bidder withdraws or modifies its bid.\n\n"
            "Section 2. Discretion of Procuring Authority.\n"
            "The Procuring Authority reserves the right to reject any or all bids without assigning any reasons whatsoever.\n\n"
            "Section 3. Annexure - Draft Service Level Agreement.\n"
            "Upon award, the successful bidder agrees to indemnify the Authority against all third-party losses."
        )
        doc = fitz.open()
        p = doc.new_page()
        p.insert_textbox(fitz.Rect(50, 50, 550, 750), tender_text)
        pdf_bytes = doc.tobytes()
        doc.close()

        res = analyze_contract("Modern_Record_Room_Tender29092020.pdf", "application/pdf", pdf_bytes)
        self.assertEqual(res.document_type, "tender_rfp")
        self.assertIn("Tender", res.document_type_label)
        self.assertEqual(res.audit_status, "COMPLETED")
        self.assertTrue(len(res.red_flags) > 0)
        # Verify procurement findings present
        categories = [f.risk_category for f in res.red_flags if f.risk_category]
        self.assertTrue(any(c in ["procurement_discretion", "penalty_damages", "indemnity"] for c in categories))

    # ── Test 34: Draft Agreement vs Executed Contract Subtypes ─────────────────
    def test_34_draft_agreement_vs_executed_contract(self):
        """
        Scenario: Distinguishes an unexecuted draft template from an executed agreement with signature blocks.
        """
        draft_text = (
            "DRAFT MASTER SERVICES AGREEMENT\n\n"
            "This Agreement is made on this [●] day of [●], 2025 by and between [Insert Company Name] "
            "and [Insert Vendor Name] (hereinafter referred to as the Parties).\n\n"
            "Clause 1. Either party may terminate for convenience with thirty days notice."
        )
        draft_res = classify_document(draft_text, filename="draft_agreement_v1.docx")
        self.assertEqual(draft_res["document_type"], "draft_agreement")

        executed_text = (
            "COMMERCIAL LEASE AGREEMENT\n\n"
            "This Agreement is executed between Lessor and Lessee on January 1, 2025.\n"
            "Clause 1. Lock-in Period of three years.\n\n"
            "IN WITNESS WHEREOF, the parties hereto have set their hands and executed this Agreement "
            "the day and year first above written.\n"
            "Signed, sealed, and delivered by Lessor:\n(Signature)\n"
            "Signed, sealed, and delivered by Lessee:\n(Signature)"
        )
        exec_res = classify_document(executed_text, filename="lease_executed_signed.pdf")
        self.assertEqual(exec_res["document_type"], "executed_contract")

    # ── Test 35: Filename Contradiction Does Not Override Content ─────────────
    def test_35_filename_contradiction_content_priority(self):
        """
        Scenario: Filename claims 'commercial_services_contract.pdf', but actual content is a court judgment.
        Document content must take priority over misleading filename.
        """
        judgment_bytes = self._create_court_judgment_pdf()
        res = analyze_contract("commercial_services_contract.pdf", "application/pdf", judgment_bytes)
        self.assertIn(res.document_type, ["court_judgment", "court_order"])
        self.assertEqual(res.audit_status, "DOCUMENT_TYPE_MISMATCH")
        self.assertEqual(res.overall_risk_score, "Not Assessed")
        self.assertEqual(len(res.red_flags), 0)

    # ── Test 36: Court Order vs Court Judgment Distinction ────────────────────
    def test_36_court_order_vs_court_judgment(self):
        """
        Scenario: Distinguishes interim court orders from final judgments.
        """
        order_text = (
            "IN THE HIGH COURT OF JUDICATURE AT BOMBAY\n"
            "INTERIM APPLICATION NO. 450 OF 2024\n"
            "CORAM: HON'BLE JUSTICE PATEL\n\n"
            "ORDER: Issue notice to the respondents returnable in two weeks. "
            "Ad-interim relief granted in terms of prayer clause (b). Stand over to 15th November 2024."
        )
        order_res = classify_document(order_text)
        self.assertEqual(order_res["document_type"], "court_order")
        self.assertFalse(order_res["is_contract"])

    # ── Test 37: Grounded Finding Schema & Backward Compatibility ─────────────
    def test_37_grounded_finding_schema_and_backward_compatibility(self):
        """
        Scenario: Verifies all new grounded evidence fields and legacy alias fields.
        """
        pdf_bytes = self._create_sample_pdf(
            "Section 8. Restraint of Trade. The Consultant shall not directly or indirectly engage in "
            "any business competing with the Company for twenty-four months following termination."
        )
        res = analyze_contract("non_compete.pdf", "application/pdf", pdf_bytes)
        self.assertTrue(len(res.red_flags) > 0)
        flag = res.red_flags[0]

        # New Grounded Schema Fields
        self.assertIsNotNone(flag.finding_id)
        self.assertIsNotNone(flag.risk_classification)
        self.assertIsNotNone(flag.verbatim_clause)
        self.assertIsNotNone(flag.statutory_provision)
        self.assertIsNotNone(flag.statutory_verification_status)
        self.assertIsNotNone(flag.legal_explanation)
        self.assertIsNotNone(flag.application_to_clause)
        self.assertIsNotNone(flag.uncertainty_or_limitation)
        self.assertIsNotNone(flag.recommended_action)

        # Legacy Backward Compatible Fields
        self.assertEqual(flag.clause_text, flag.verbatim_clause)
        self.assertEqual(flag.explanation, flag.legal_explanation)
        self.assertEqual(flag.recommendation, flag.recommended_action)
        self.assertIsNotNone(flag.page_ref)

    # ── Test 38: Statutory Verification Catalog ───────────────────────────────
    def test_38_statutory_verification_catalog(self):
        """
        Scenario: Verified statutory provisions are marked verified; unsupported are marked unverified.
        """
        from services.contracts_service import _resolve_statutory_verification

        # Verified Section 27 Indian Contract Act
        law1, prov1, status1 = _resolve_statutory_verification("Section 27, Indian Contract Act")
        self.assertEqual(status1, "verified")
        self.assertIn("Section 27", prov1)

        # Verified Section 12(5) Arbitration Act
        law2, prov2, status2 = _resolve_statutory_verification("Section 12(5)")
        self.assertEqual(status2, "verified")

        # Unverified arbitrary or foreign statutory provision
        law3, prov3, status3 = _resolve_statutory_verification("Section 999 of Hypothetical Act 2099")
        self.assertEqual(status3, "unverified")

        # Empty / None
        law4, prov4, status4 = _resolve_statutory_verification(None)
        self.assertEqual(status4, "not_applicable")

    # ── Test 39: Commercial Risk Separation from Legal Conclusions ─────────────
    def test_39_commercial_risk_separation_from_legal_conclusions(self):
        """
        Scenario: Separates potential_commercial_risk from legal conclusions requiring review.
        """
        from services.contracts_service import _determine_risk_classification

        # Discretionary procurement term -> potential_commercial_risk
        class1 = _determine_risk_classification(
            "procurement_discretion",
            "The Authority may reject any bid without assigning reasons."
        )
        self.assertEqual(class1, "potential_commercial_risk")

        # Liquidated damages clause -> possible_legal_concern
        class2 = _determine_risk_classification(
            "penalty_damages",
            "Client shall pay liquidated damages equal to 100% of the remaining contract fees."
        )
        self.assertEqual(class2, "possible_legal_concern")

        # Post-term non-compete -> legal_conclusion_requiring_review
        class3 = _determine_risk_classification(
            "restrictive_covenants",
            "Consultant shall not compete with Company for 24 months."
        )
        self.assertEqual(class3, "legal_conclusion_requiring_review")

    # ── Test 40: Score Breakdown Calculation & BIS Tender Scenario ────────────
    def test_40_score_breakdown_calculation_and_bis_scenario(self):
        """
        Scenario: Validates ScoreBreakdown calculation.
        BIS Scenario: 3 High findings (15 pts) + 4 Medium findings (12 pts) = 27 points.
        """
        from services.contracts_service import _calculate_score_and_breakdown

        sample_flags = [
            RedFlag(risk_level="high", risk_category="indemnity", clause_text="c1", explanation="e1"),
            RedFlag(risk_level="high", risk_category="liability", clause_text="c2", explanation="e2"),
            RedFlag(risk_level="high", risk_category="restrictive_covenants", clause_text="c3", explanation="e3"),
            RedFlag(risk_level="medium", risk_category="termination", clause_text="c4", explanation="e4"),
            RedFlag(risk_level="medium", risk_category="dispute_jurisdiction", clause_text="c5", explanation="e5"),
            RedFlag(risk_level="medium", risk_category="procurement_discretion", clause_text="c6", explanation="e6"),
            RedFlag(risk_level="medium", risk_category="payment_terms", clause_text="c7", explanation="e7"),
        ]

        overall, breakdown, counts = _calculate_score_and_breakdown(
            verified_flags=sample_flags,
            is_contract=True,
            audit_status="COMPLETED",
            document_type_label="Tender / Request for Proposal (RFP)",
        )

        self.assertEqual(overall, "High")
        self.assertEqual(breakdown.numerical_score, 27)
        self.assertEqual(breakdown.high_count, 3)
        self.assertEqual(breakdown.medium_count, 4)
        self.assertEqual(breakdown.low_count, 0)
        self.assertEqual(len(breakdown.contributing_findings), 7)
        self.assertIn("27 pts", breakdown.risk_rationale)

    # ── Test 41: Fact-Grounded Summary Does Not Hallucinate Indemnity ──────────
    def test_41_evidence_based_summary_no_hallucinated_indemnity(self):
        """
        Scenario: A contract with ONLY non-compete and renewal clauses does NOT mention indemnity in the summary.
        """
        from services.contracts_service import _generate_evidence_based_summary, _calculate_score_and_breakdown

        flags = [
            RedFlag(
                title="Post-Termination Non-Compete",
                risk_level="high",
                risk_category="restrictive_covenants",
                risk_classification="legal_conclusion_requiring_review",
                clause_text="Consultant shall not compete for 24 months.",
                explanation="Restraint of trade.",
            ),
            RedFlag(
                title="Automatic Renewal",
                risk_level="medium",
                risk_category="renewal",
                risk_classification="potential_commercial_risk",
                clause_text="Agreement automatically renews for successive 12-month terms.",
                explanation="Automatic rollover risk.",
            ),
        ]
        overall, breakdown, counts = _calculate_score_and_breakdown(flags, True, "COMPLETED", "Commercial Contract")
        summary = _generate_evidence_based_summary(
            verified_flags=flags,
            doc_type="commercial_contract",
            doc_label="Commercial Contract / Agreement",
            overall_score=overall,
            numerical_score=breakdown.numerical_score,
            filename="simple_agreement.pdf",
            score_breakdown=breakdown,
        )

        self.assertNotIn("indemnity", summary.lower())
        self.assertNotIn("indemnification", summary.lower())
        self.assertIn("restrictive covenants", summary.lower())
        self.assertIn("renewal", summary.lower())

    # ── Test 42: Zero Findings Legal Safety Disclaimer ────────────────────────
    def test_42_zero_findings_safety_disclaimer(self):
        """
        Scenario: A contract with 0 red flags receives Low Risk with an explicit disclaimer.
        Absence of detected red flags does not guarantee legal safety or enforceability.
        """
        from services.contracts_service import _calculate_score_and_breakdown

        overall, breakdown, counts = _calculate_score_and_breakdown(
            verified_flags=[],
            is_contract=True,
            audit_status="COMPLETED",
            document_type_label="Commercial Contract / Agreement",
        )
        self.assertEqual(overall, "Low")
        self.assertEqual(breakdown.numerical_score, 0)
        self.assertIn("Absence of detected red flags does not guarantee legal compliance", breakdown.risk_rationale)


if __name__ == "__main__":
    unittest.main()


