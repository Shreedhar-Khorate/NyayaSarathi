"""
Legal Document OCR Processor & Orchestrator.
Routes input documents to PDFExtractor (digital/scanned/mixed), DOCXExtractor,
or ImageExtractor, assembling a unified document extraction payload.
"""

import os
import logging
from typing import Dict, Any
from services.ocr.pdf_extractor import PDFExtractor
from services.ocr.docx_extractor import DOCXExtractor
from services.ocr.detector import DocumentDetector
from services.ocr.image_extractor import ImageExtractor

logger = logging.getLogger("nyayasarathi.ocr.processor")


class LegalOCRProcessor:
    @staticmethod
    def process_document(file_path: str, filename: str) -> Dict[str, Any]:
        logger.info(f"Starting processing for file: {filename}")
        ext = os.path.splitext(filename)[1].lower()

        pages_data = []
        extraction_method = "digital"
        document_type = "unknown"

        if ext == ".pdf":
            detection = DocumentDetector.detect_pdf_type(file_path)
            document_type = detection["pdf_type"].lower()

            logger.info("Routing to PDFExtractor")
            extractor = PDFExtractor()
            pages_data = extractor.extract_text(file_path, detection)

            if document_type in ["scanned_pdf", "mixed_pdf"]:
                extraction_method = "paddleocr_mixed"
        elif ext in [".docx", ".doc"]:
            logger.info("Routing to DOCXExtractor")
            pages_data = DOCXExtractor.extract_text(file_path)
            document_type = "docx"
        else:
            logger.info("Routing to ImageExtractor (PaddleOCR)")
            extractor = ImageExtractor()
            pages_data = extractor.extract_text(file_path)
            extraction_method = "paddleocr"
            document_type = "image"

        full_text = "\n\n".join([page["text"] for page in pages_data])

        return {
            "document_type": document_type,
            "pages": len(pages_data),
            "extraction_method": extraction_method,
            "text": full_text,
            "pages_data": pages_data
        }

    # Backward compatibility alias
    process_digital = process_document


# Alias for backward compatibility
DocumentProcessor = LegalOCRProcessor

__all__ = ["LegalOCRProcessor", "DocumentProcessor"]
