"""
Document Type Detector for Legal Documents.
Classifies PDFs into TEXT_PDF (digital), SCANNED_PDF (image-only), or MIXED_PDF.
"""

import pymupdf as fitz
import logging

logger = logging.getLogger("nyayasarathi.ocr.detector")


class DocumentDetector:
    @staticmethod
    def detect_pdf_type(file_path: str) -> dict:
        doc = fitz.open(file_path)
        pages_classification = []

        has_text_pages = False
        has_scanned_pages = False

        logger.info(f"Pages detected: {len(doc)}")

        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text = page.get_text().strip()

            # Heuristic: less than 50 chars of text means it's likely a scanned image
            if len(text) < 50:
                images = page.get_images(full=True)
                if images:
                    pages_classification.append("scanned")
                    has_scanned_pages = True
                else:
                    pages_classification.append("blank")
            else:
                pages_classification.append("text")
                has_text_pages = True

        if has_text_pages and has_scanned_pages:
            pdf_type = "MIXED_PDF"
        elif has_scanned_pages:
            pdf_type = "SCANNED_PDF"
        else:
            pdf_type = "TEXT_PDF"

        logger.info(f"File type detected: {pdf_type}")

        return {
            "pdf_type": pdf_type,
            "pages_classification": pages_classification
        }


__all__ = ["DocumentDetector"]
