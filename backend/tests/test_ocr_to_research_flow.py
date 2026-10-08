"""
End-to-End Integration Tests for OCR -> Legal Research Flow.
Verifies all 6 core integration requirements:
1. Digital PDF -> OCR/extraction -> Legal Research
2. Scanned PDF -> OCR -> Legal Research
3. DOCX -> extraction -> Legal Research
4. Image -> OCR -> Legal Research
5. OCR success + ingestion failure handling
6. Retry ingestion without rerunning OCR (Idempotency)
"""

import io
import os
import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
import pymupdf as fitz
import docx

from main import app
from services.rag_retrieval import get_rag_retrieval_engine
from services.document_processor import get_document_processor, get_document_by_id


class TestOCRToLegalResearchFlow(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_flow_digital_pdf_to_legal_research(self):
        # 1. Generate digital PDF with distinct legal content
        doc = fitz.open()
        p1 = doc.new_page(width=595, height=842)
        p1.insert_text(
            (50, 80),
            "IN THE HIGH COURT OF DELHI AT NEW DELHI\n\n"
            "W.P.(C) No. 8921/2026\n\n"
            "M/s Horizon Infra Pvt Ltd vs Union of India & Anr.\n\n"
            "1. This writ petition challenges the cancellation order dated 04.01.2026 passed by respondent authority.\n\n"
            "2. The primary ground of challenge is violation of principles of natural justice since no show cause notice was issued before debarment.",
            fontsize=11,
        )
        pdf_bytes = doc.write()
        doc.close()

        # 2. Upload to OCR endpoint (POST /api/ocr/process)
        ocr_res = self.client.post(
            "/api/ocr/process",
            files={"file": ("horizon_writ_petition.pdf", pdf_bytes, "application/pdf")},
        )
        self.assertEqual(ocr_res.status_code, 200)
        ocr_data = ocr_res.json()
        self.assertEqual(ocr_data["status"], "completed")
        self.assertIn("Horizon Infra", ocr_data["text"])
        doc_id = ocr_data["document_id"]

        # 3. Handoff to Legal Research (POST /api/ocr/send-to-research)
        research_res = self.client.post(
            "/api/ocr/send-to-research",
            json={
                "document_id": doc_id,
                "filename": ocr_data["filename"],
                "document_type": ocr_data["document_type"],
                "pages": ocr_data["pages"],
                "extraction_method": ocr_data["extraction_method"],
                "text": ocr_data["text"],
                "pages_data": ocr_data["pages_data"],
                "title": "Horizon Infra Writ Petition 2026",
            },
        )
        self.assertEqual(research_res.status_code, 201)
        research_meta = research_res.json()
        self.assertEqual(research_meta["id"], doc_id)
        self.assertEqual(research_meta["status"], "indexed")
        self.assertTrue(research_meta["total_chunks"] >= 1)

        # 4. Check document is listed in Legal Research catalog
        catalog_res = self.client.get("/api/qa/documents")
        self.assertEqual(catalog_res.status_code, 200)
        all_ids = [d["id"] for d in catalog_res.json()["documents"]]
        self.assertIn(doc_id, all_ids)

        # 5. Check document details & chunks are stored
        details_res = self.client.get(f"/api/qa/documents/{doc_id}")
        self.assertEqual(details_res.status_code, 200)
        self.assertTrue(len(details_res.json()["chunks"]) >= 1)

        # 6. Verify evidence retrieval works on this OCR document
        engine = get_rag_retrieval_engine()
        pack = engine.retrieve_evidence(
            question="What is the primary ground of challenge in this writ petition?",
            document_ids=[doc_id],
            top_k=3,
        )
        self.assertTrue(len(pack.chunks) >= 1)
        self.assertIn("natural justice", pack.chunks[0].text.lower())
        self.assertEqual(pack.chunks[0].document_id, doc_id)

    def test_flow_scanned_pdf_to_legal_research(self):
        # 1. Create a scanned PDF representation with image extraction mock
        doc = fitz.open()
        page = doc.new_page(width=595, height=842)
        # Create small pixmap image and insert into PDF
        pix = fitz.Pixmap(fitz.csRGB, (0, 0, 100, 100), 0)
        pix.clear_with(255)
        img_bytes = pix.tobytes("png")
        page.insert_image(fitz.Rect(50, 50, 300, 300), stream=img_bytes)
        pdf_bytes = doc.write()
        doc.close()

        scanned_text = (
            "COMMISSIONER OF INCOME TAX vs M/S TECHVENTURES LTD\n"
            "ITA No. 1290 of 2025\n"
            "Held: Disallowance under Section 14A cannot exceed exempt income earned during the assessment year."
        )

        with patch("services.ocr.pdf_extractor.PDFExtractor.extract_text") as mock_extract:
            mock_extract.return_value = [
                {
                    "page_number": 1,
                    "text": scanned_text,
                    "confidence": 0.89,
                    "blocks": [
                        {"text": "COMMISSIONER OF INCOME TAX", "confidence": 0.92, "bbox": [50, 60, 300, 80]},
                        {"text": "Held: Disallowance under Section 14A", "confidence": 0.88, "bbox": [50, 100, 400, 120]},
                    ],
                }
            ]

            ocr_res = self.client.post(
                "/api/ocr/process",
                files={"file": ("scanned_tax_appeal.pdf", pdf_bytes, "application/pdf")},
            )
            self.assertEqual(ocr_res.status_code, 200)
            ocr_data = ocr_res.json()
            self.assertEqual(ocr_data["status"], "completed")
            doc_id = ocr_data["document_id"]

            # Handoff to Legal Research
            research_res = self.client.post(
                "/api/ocr/send-to-research",
                json={
                    "document_id": doc_id,
                    "filename": ocr_data["filename"],
                    "document_type": ocr_data["document_type"],
                    "pages": ocr_data["pages"],
                    "extraction_method": ocr_data["extraction_method"],
                    "text": ocr_data["text"],
                    "pages_data": ocr_data["pages_data"],
                    "title": "Tax Appeal Scanned Order",
                },
            )
            self.assertEqual(research_res.status_code, 201)
            self.assertEqual(research_res.json()["status"], "indexed")

            # Verify retrieval works on scanned PDF text
            engine = get_rag_retrieval_engine()
            pack = engine.retrieve_evidence(
                question="Can disallowance under Section 14A exceed exempt income?",
                document_ids=[doc_id],
                top_k=2,
            )
            self.assertTrue(len(pack.chunks) >= 1)
            self.assertIn("section 14a", pack.chunks[0].text.lower())

    def test_flow_docx_to_legal_research(self):
        # 1. Create in-memory DOCX
        doc = docx.Document()
        doc.add_heading("IN THE SUPREME COURT OF INDIA", level=1)
        doc.add_paragraph("Special Leave Petition (Civil) No. 4012 of 2026.")
        doc.add_paragraph("The court held that compensation under Section 166 of the Motor Vehicles Act must account for future prospects.")
        docx_io = io.BytesIO()
        doc.save(docx_io)
        docx_bytes = docx_io.getvalue()

        # 2. Process via OCR
        ocr_res = self.client.post(
            "/api/ocr/process",
            files={
                "file": (
                    "motor_accident_slp.docx",
                    docx_bytes,
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
            },
        )
        self.assertEqual(ocr_res.status_code, 200)
        ocr_data = ocr_res.json()
        doc_id = ocr_data["document_id"]

        # 3. Send to Legal Research
        send_res = self.client.post(
            "/api/ocr/send-to-research",
            json={
                "document_id": doc_id,
                "filename": ocr_data["filename"],
                "document_type": ocr_data["document_type"],
                "pages": ocr_data["pages"],
                "extraction_method": ocr_data["extraction_method"],
                "text": ocr_data["text"],
                "pages_data": ocr_data["pages_data"],
            },
        )
        self.assertEqual(send_res.status_code, 201)
        self.assertEqual(send_res.json()["status"], "indexed")

        # 4. Verify retrieval
        engine = get_rag_retrieval_engine()
        pack = engine.retrieve_evidence(
            question="What Act and Section was compensation calculated under?",
            document_ids=[doc_id],
            top_k=2,
        )
        self.assertTrue(len(pack.chunks) >= 1)
        self.assertIn("motor vehicles act", pack.chunks[0].text.lower())

    def test_flow_image_to_legal_research(self):
        # Direct handoff of image OCR result
        doc_id = "img_ocr_test_doc_004"
        payload = {
            "document_id": doc_id,
            "filename": "scanned_high_court_order.png",
            "document_type": "image",
            "pages": 1,
            "extraction_method": "paddleocr",
            "text": "HIGH COURT OF BOMBAY\nORDER\nNotice is returnable on 24th February 2026. Ad-interim relief granted in terms of prayer clause (b).",
            "pages_data": [
                {
                    "page_number": 1,
                    "text": "HIGH COURT OF BOMBAY\nORDER\nNotice is returnable on 24th February 2026. Ad-interim relief granted in terms of prayer clause (b).",
                    "confidence": 0.94,
                    "blocks": [
                        {"text": "HIGH COURT OF BOMBAY", "confidence": 0.96, "bbox": [50, 50, 250, 70]},
                        {"text": "ORDER", "confidence": 0.98, "bbox": [50, 90, 150, 110]},
                        {"text": "Notice is returnable on 24th February 2026.", "confidence": 0.92, "bbox": [50, 130, 350, 150]},
                    ],
                }
            ],
            "title": "Bombay HC Ad-Interim Order",
        }

        res = self.client.post("/api/ocr/send-to-research", json=payload)
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.json()["id"], doc_id)
        self.assertEqual(res.json()["total_pages"], 1)

        # Verify retrieval finds the returnable date
        engine = get_rag_retrieval_engine()
        pack = engine.retrieve_evidence(
            question="When is notice returnable?",
            document_ids=[doc_id],
            top_k=1,
        )
        self.assertTrue(len(pack.chunks) >= 1)
        self.assertIn("24th february 2026", pack.chunks[0].text.lower())

    def test_ocr_success_then_ingestion_failure_and_retry(self):
        # 1. Produce valid OCR result
        doc = fitz.open()
        p = doc.new_page(width=595, height=842)
        p.insert_text((50, 80), "DISTRICT COURT COMMERCIAL DIVISION: Suit No. 102/2026 for Recovery.", fontsize=12)
        pdf_bytes = doc.write()
        doc.close()

        ocr_res = self.client.post(
            "/api/ocr/process",
            files={"file": ("commercial_suit.pdf", pdf_bytes, "application/pdf")},
        )
        self.assertEqual(ocr_res.status_code, 200)
        ocr_data = ocr_res.json()
        doc_id = ocr_data["document_id"]
        # OCR result is complete and available
        self.assertEqual(ocr_data["status"], "completed")

        # 2. Simulate Ingestion Failure (e.g. empty text submitted or validation fail)
        invalid_payload = {
            "document_id": doc_id,
            "filename": ocr_data["filename"],
            "text": "   ",  # Blank text causes 400 validation error
            "pages": 1,
            "pages_data": [],
        }
        fail_res = self.client.post("/api/ocr/send-to-research", json=invalid_payload)
        self.assertEqual(fail_res.status_code, 400)
        self.assertIn("empty", fail_res.json()["error"].lower())

        # Verify original OCR data remains untouched and ready
        self.assertTrue(len(ocr_data["text"]) > 0)

        # 3. Retry Ingestion using original OCR result without re-uploading or re-running OCR
        valid_payload = {
            "document_id": doc_id,
            "filename": ocr_data["filename"],
            "document_type": ocr_data["document_type"],
            "pages": ocr_data["pages"],
            "extraction_method": ocr_data["extraction_method"],
            "text": ocr_data["text"],
            "pages_data": ocr_data["pages_data"],
            "title": "Commercial Suit 102/2026",
        }
        retry_res = self.client.post("/api/ocr/send-to-research", json=valid_payload)
        self.assertEqual(retry_res.status_code, 201)
        self.assertEqual(retry_res.json()["id"], doc_id)
        self.assertEqual(retry_res.json()["status"], "indexed")

    def test_idempotent_retry_without_rerunning_ocr(self):
        # Test that user can retry ingestion multiple times safely without duplicate chunk errors
        doc_id = "retry_test_doc_005"
        payload = {
            "document_id": doc_id,
            "filename": "retry_test.pdf",
            "text": "Clause 1: The arbitration shall be conducted in New Delhi under the Arbitration and Conciliation Act 1996.",
            "pages": 1,
            "pages_data": [
                {
                    "page_number": 1,
                    "text": "Clause 1: The arbitration shall be conducted in New Delhi under the Arbitration and Conciliation Act 1996.",
                    "confidence": 0.91,
                    "blocks": [],
                }
            ],
        }

        # Attempt 1
        res1 = self.client.post("/api/ocr/send-to-research", json=payload)
        self.assertEqual(res1.status_code, 201)

        # Attempt 2 (Retry)
        res2 = self.client.post("/api/ocr/send-to-research", json=payload)
        self.assertEqual(res2.status_code, 201)
        self.assertEqual(res2.json()["id"], doc_id)

        # Attempt 3 (Retry again)
        res3 = self.client.post("/api/ocr/send-to-research", json=payload)
        self.assertEqual(res3.status_code, 201)

        # Document still has exactly 1 set of chunks (no duplicates)
        doc = get_document_by_id(doc_id)
        self.assertIsNotNone(doc)
        self.assertEqual(doc["total_chunks"], 1)


if __name__ == "__main__":
    unittest.main()
