"""
PDF Text & Scanned Image Extractor.
Extracts digital text blocks using PyMuPDF and falls back to rendering at 250 DPI
and running OpenCV preprocessing + PaddleOCR on scanned pages.
"""

import pymupdf as fitz
import os
import logging
from typing import List, Dict, Any
from services.ocr.detector import DocumentDetector
from services.ocr.image_preprocessor import ImagePreprocessor
from services.ocr.ocr_engine import OCREngine

logger = logging.getLogger("nyayasarathi.ocr.pdf_extractor")


class PDFExtractor:
    def __init__(self):
        self.ocr_engine = None

    def _get_ocr_engine(self):
        if self.ocr_engine is None:
            self.ocr_engine = OCREngine()
        return self.ocr_engine

    def extract_text(self, file_path: str, detection: dict = None) -> List[Dict[str, Any]]:
        doc = fitz.open(file_path)
        pages_data = []

        if detection is None:
            detection = DocumentDetector.detect_pdf_type(file_path)

        page_types = detection["pages_classification"]

        dpi = int(os.getenv("PDF_RENDER_DPI", "250"))
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        temp_dir = os.path.join(base_dir, "data", "temp_ocr")
        os.makedirs(temp_dir, exist_ok=True)

        for page_num in range(len(doc)):
            page_type = page_types[page_num]
            logger.info(f"Page {page_num + 1}: {page_type}")

            if page_type == "text":
                page = doc.load_page(page_num)
                # Extract blocks (x0, y0, x1, y1, text, block_no, block_type)
                # block_type 0 = text, 1 = image
                raw_blocks = page.get_text("blocks")
                blocks = []
                if isinstance(raw_blocks, list):
                    for b in raw_blocks:
                        if isinstance(b, (list, tuple)) and len(b) >= 7 and b[6] == 0:  # text block
                            blocks.append({
                                "text": b[4].strip(),
                                "confidence": 1.0,  # Digital text is 100% confident
                                "bbox": [int(b[0]), int(b[1]), int(b[2]), int(b[3])]
                            })
                elif isinstance(raw_blocks, str):
                    blocks.append({
                        "text": raw_blocks.strip(),
                        "confidence": 1.0,
                        "bbox": [0, 0, 100, 100]
                    })

                from services.ocr.reading_order import ReadingOrder
                sorted_blocks = ReadingOrder.sort_blocks(blocks)
                full_text = "\n".join([b["text"] for b in sorted_blocks])

                pages_data.append({
                    "page_number": page_num + 1,
                    "text": full_text,
                    "confidence": None,
                    "blocks": sorted_blocks
                })
            elif page_type == "scanned":
                logger.info(f"Rendering page {page_num + 1} to image for OCR")
                page = doc.load_page(page_num)

                # Render page to image
                pix = page.get_pixmap(dpi=dpi)
                temp_img_path = os.path.join(temp_dir, f"page_{page_num}_{os.getpid()}.png")
                pix.save(temp_img_path)

                # Preprocess and OCR
                processed_img = ImagePreprocessor.preprocess_image(temp_img_path)
                engine = self._get_ocr_engine()
                ocr_result = engine.extract(processed_img)

                # Clean up temp file
                if os.path.exists(temp_img_path):
                    try:
                        os.remove(temp_img_path)
                    except OSError:
                        pass

                pages_data.append({
                    "page_number": page_num + 1,
                    "text": ocr_result["text"],
                    "confidence": ocr_result["confidence"],
                    "blocks": ocr_result["blocks"]
                })
            else:
                page = doc.load_page(page_num)
                fallback_txt = page.get_text().strip()
                pages_data.append({
                    "page_number": page_num + 1,
                    "text": fallback_txt if fallback_txt else "[Blank Page]",
                    "confidence": 1.0 if fallback_txt else None,
                    "blocks": []
                })

        return pages_data


__all__ = ["PDFExtractor"]
