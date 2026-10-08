"""
NyayaSarathi Legal Document OCR Comprehensive Test Suite.
Tests:
- Document Type Detector (Digital, Scanned, Mixed)
- Layout Analyzer (Column detection, gutters, legal regions)
- Reading Order (Line grouping, two-column order preservation)
- File Validator (MIME types, extensions, size constraints)
- Extractors (PDF, DOCX, Image)
- LegalOCRProcessor pipeline coordination
- FastAPI Endpoints (/api/ocr/process, /api/legal-documents/process, /api/ocr/upload)
"""

import os
import io
import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import HTTPException
import pymupdf as fitz
import docx

from main import app
from schemas.ocr import Block, PageData, OCRDocumentResponse
from services.ocr import (
    DocumentDetector,
    LayoutAnalyzer,
    ReadingOrder,
    PDFExtractor,
    DOCXExtractor,
    ImageExtractor,
    LegalOCRProcessor,
    validate_file,
)


class TestDocumentDetector(unittest.TestCase):
    @patch("services.ocr.detector.fitz.open")
    def test_detect_text_pdf(self, mock_fitz_open):
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_page.get_text.return_value = "This is a detailed legal submission. " * 10
        mock_doc.__len__.return_value = 1
        mock_doc.load_page.return_value = mock_page
        mock_fitz_open.return_value = mock_doc

        result = DocumentDetector.detect_pdf_type("dummy.pdf")
        self.assertEqual(result["pdf_type"], "TEXT_PDF")
        self.assertEqual(result["pages_classification"], ["text"])

    @patch("services.ocr.detector.fitz.open")
    def test_detect_scanned_pdf(self, mock_fitz_open):
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_page.get_text.return_value = "Short"
        mock_page.get_images.return_value = [("img1",)]
        mock_doc.__len__.return_value = 1
        mock_doc.load_page.return_value = mock_page
        mock_fitz_open.return_value = mock_doc

        result = DocumentDetector.detect_pdf_type("dummy.pdf")
        self.assertEqual(result["pdf_type"], "SCANNED_PDF")
        self.assertEqual(result["pages_classification"], ["scanned"])

    @patch("services.ocr.detector.fitz.open")
    def test_detect_mixed_pdf(self, mock_fitz_open):
        mock_doc = MagicMock()
        mock_p1 = MagicMock()
        mock_p1.get_text.return_value = "Digital text page in court filing. " * 8
        mock_p2 = MagicMock()
        mock_p2.get_text.return_value = "1"
        mock_p2.get_images.return_value = [("scan_img",)]
        mock_doc.__len__.return_value = 2
        mock_doc.load_page.side_effect = [mock_p1, mock_p2]
        mock_fitz_open.return_value = mock_doc

        result = DocumentDetector.detect_pdf_type("dummy.pdf")
        self.assertEqual(result["pdf_type"], "MIXED_PDF")
        self.assertEqual(result["pages_classification"], ["text", "scanned"])


class TestLayoutAnalyzer(unittest.TestCase):
    def test_detect_single_column(self):
        blocks = [
            {"text": "A", "bbox": [10, 10, 100, 30]},
            {"text": "B", "bbox": [10, 40, 100, 60]},
            {"text": "C", "bbox": [10, 70, 100, 90]},
        ]
        columns = LayoutAnalyzer.detect_columns(blocks)
        self.assertEqual(len(columns), 1)
        self.assertEqual(len(columns[0]), 3)

    def test_detect_two_columns_with_gutter(self):
        blocks = [
            {"text": "Col1 Line1", "bbox": [0, 0, 100, 20]},
            {"text": "Col1 Line2", "bbox": [0, 25, 100, 45]},
            {"text": "Col2 Line1", "bbox": [150, 0, 250, 20]},
            {"text": "Col2 Line2", "bbox": [150, 25, 250, 45]},
        ]
        columns = LayoutAnalyzer.detect_columns(blocks)
        self.assertEqual(len(columns), 2)
        self.assertEqual(columns[0][0]["text"], "Col1 Line1")
        self.assertEqual(columns[1][0]["text"], "Col2 Line1")

    def test_classify_legal_regions(self):
        cit_block = {"text": "[2026] 9 S.C.R. 112 : 2026 INSC 864", "bbox": [50, 50, 300, 70]}
        self.assertEqual(LayoutAnalyzer.classify_block_region(cit_block), "citation")

        case_block = {"text": "Civil Appeal No. 10738 of 2026", "bbox": [50, 80, 280, 100]}
        self.assertEqual(LayoutAnalyzer.classify_block_region(case_block), "case_number")

        bench_block = {"text": "[N.V. Anjaria, Hon'ble Justice]", "bbox": [50, 110, 250, 130]}
        self.assertEqual(LayoutAnalyzer.classify_block_region(bench_block), "bench")

        date_block = {"text": "14 August 2026", "bbox": [50, 140, 150, 160]}
        self.assertEqual(LayoutAnalyzer.classify_block_region(date_block), "date")

        heading_block = {"text": "JUDGMENT", "bbox": [50, 170, 120, 190]}
        self.assertEqual(LayoutAnalyzer.classify_block_region(heading_block), "heading")


class TestReadingOrder(unittest.TestCase):
    def test_reading_order_two_columns(self):
        blocks = [
            {"text": "Right 2", "bbox": [150, 25, 250, 45]},
            {"text": "Left 1", "bbox": [0, 0, 100, 20]},
            {"text": "Right 1", "bbox": [150, 0, 250, 20]},
            {"text": "Left 2", "bbox": [0, 25, 100, 45]},
        ]
        sorted_blocks = ReadingOrder.sort_blocks(blocks)
        self.assertEqual(len(sorted_blocks), 4)
        self.assertEqual(sorted_blocks[0]["text"], "Left 1")
        self.assertEqual(sorted_blocks[1]["text"], "Left 2")
        self.assertEqual(sorted_blocks[2]["text"], "Right 1")
        self.assertEqual(sorted_blocks[3]["text"], "Right 2")

    def test_reading_order_same_line_sorting(self):
        blocks = [
            {"text": "Second", "bbox": [60, 10, 120, 30]},
            {"text": "First", "bbox": [10, 10, 50, 30]},
        ]
        sorted_blocks = ReadingOrder.sort_blocks(blocks)
        self.assertEqual(sorted_blocks[0]["text"], "First")
        self.assertEqual(sorted_blocks[1]["text"], "Second")


class TestExtractorsAndProcessors(unittest.TestCase):
    @patch("services.ocr.docx_extractor.docx.Document")
    def test_docx_extractor(self, mock_doc_cls):
        mock_doc = MagicMock()
        mock_doc.paragraphs = [MagicMock(text="Supreme Court of India"), MagicMock(text="Order dated 2026")]
        mock_doc.tables = []
        mock_doc_cls.return_value = mock_doc

        pages = DOCXExtractor.extract_text("sample.docx")
        self.assertEqual(len(pages), 1)
        self.assertIn("Supreme Court of India", pages[0]["text"])

    @patch("services.ocr.image_preprocessor.ImagePreprocessor.preprocess_image")
    @patch("services.ocr.image_extractor.OCREngine")
    def test_image_extractor(self, mock_engine_cls, mock_preproc):
        mock_preproc.return_value = MagicMock()
        mock_engine = MagicMock()
        mock_engine.extract.return_value = {
            "text": "High Court Affidavit Text",
            "confidence": 0.94,
            "blocks": [{"text": "High Court Affidavit Text", "confidence": 0.94, "bbox": [10, 10, 200, 30]}],
        }
        mock_engine_cls.return_value = mock_engine

        extractor = ImageExtractor()
        pages = extractor.extract_text("affidavit.png")
        self.assertEqual(len(pages), 1)
        self.assertEqual(pages[0]["text"], "High Court Affidavit Text")
        self.assertEqual(pages[0]["confidence"], 0.94)

    @patch("services.ocr.ocr_processor.DocumentDetector.detect_pdf_type")
    @patch("services.ocr.ocr_processor.PDFExtractor")
    def test_processor_routes_pdf(self, mock_extractor_cls, mock_detect):
        mock_detect.return_value = {"pdf_type": "TEXT_PDF", "pages_classification": ["text"]}
        mock_inst = MagicMock()
        mock_inst.extract_text.return_value = [{"page_number": 1, "text": "Extracted PDF content", "blocks": []}]
        mock_extractor_cls.return_value = mock_inst

        result = LegalOCRProcessor.process_document("doc.pdf", "doc.pdf")
        self.assertEqual(result["document_type"], "text_pdf")
        self.assertEqual(result["extraction_method"], "digital")
        self.assertEqual(result["pages"], 1)
        self.assertEqual(result["text"], "Extracted PDF content")


class TestFastAPIOcrEndpoints(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_ocr_process_endpoint_validation(self):
        # Sending unsupported file format (.exe)
        response = self.client.post(
            "/api/ocr/process",
            files={"file": ("malicious.exe", b"binarycontent", "application/octet-stream")},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Unsupported file format", response.json()["error"])

    def test_ocr_process_digital_pdf(self):
        # Generate an in-memory 1-page digital PDF using PyMuPDF
        doc = fitz.open()
        page = doc.new_page(width=595, height=842)
        text = "IN THE SUPREME COURT OF INDIA\nCRIMINAL APPELLATE JURISDICTION\nSPECIAL LEAVE PETITION"
        page.insert_text((50, 100), text, fontsize=12)
        pdf_bytes = doc.write()
        doc.close()

        response = self.client.post(
            "/api/ocr/process",
            files={"file": ("supreme_court_pleading.pdf", pdf_bytes, "application/pdf")},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "completed")
        self.assertEqual(data["document_type"], "text_pdf")
        self.assertEqual(data["pages"], 1)
        self.assertIn("SUPREME COURT OF INDIA", data["text"])
        self.assertTrue(len(data["pages_data"]) > 0)

    def test_legal_documents_endpoint_alias(self):
        # Verify POST /api/legal-documents/process works identically
        doc = fitz.open()
        page = doc.new_page(width=595, height=842)
        page.insert_text((50, 100), "IN THE HIGH COURT OF JUDICATURE AT BOMBAY - BENCH AT NAGPUR\nWRIT PETITION UNDER ARTICLE 226 OF THE CONSTITUTION OF INDIA", fontsize=12)
        pdf_bytes = doc.write()
        doc.close()

        response = self.client.post(
            "/api/legal-documents/process",
            files={"file": ("bombay_hc_order.pdf", pdf_bytes, "application/pdf")},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "completed")
        self.assertIn("BOMBAY", data["text"])

    def test_ocr_process_docx(self):
        # Generate in-memory DOCX
        doc = docx.Document()
        doc.add_heading("IN THE HIGH COURT OF DELHI", level=1)
        doc.add_paragraph("Petition under Article 226 of Constitution of India.")
        docx_io = io.BytesIO()
        doc.save(docx_io)
        docx_bytes = docx_io.getvalue()

        response = self.client.post(
            "/api/ocr/process",
            files={
                "file": (
                    "writ_petition.docx",
                    docx_bytes,
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
            },
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["document_type"], "docx")
        self.assertIn("DELHI", data["text"])


if __name__ == "__main__":
    unittest.main()
