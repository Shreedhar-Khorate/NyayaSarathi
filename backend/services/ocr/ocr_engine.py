"""
PaddleOCR Engine Wrapper for Legal Document Analysis.
Initializes PaddleOCR with English angle classification and extracts text with bounding boxes.
"""

try:
    from paddleocr import PaddleOCR
except ImportError:
    PaddleOCR = None
import numpy as np
import logging
import time

logger = logging.getLogger("nyayasarathi.ocr.engine")


class OCREngine:
    def __init__(self):
        # Initialize PaddleOCR
        if PaddleOCR is None:
            raise RuntimeError("PaddleOCR is not installed. Please install paddleocr and paddlepaddle to use OCR features.")
        # Using stable 2.8.1 arguments
        self.ocr = PaddleOCR(use_angle_cls=True, lang='en', use_gpu=False, show_log=False)

    def extract(self, image: np.ndarray) -> dict:
        logger.info("Starting OCR processing on image segment...")
        start_time = time.time()

        result = self.ocr.ocr(image, cls=True)

        blocks = []
        full_text = []

        # PaddleOCR returns a list of results, result[0] contains the actual lines
        if result and len(result) > 0 and result[0] is not None:
            for line in result[0]:
                bbox = line[0]
                text = line[1][0]
                confidence = line[1][1]

                # Bbox comes as 4 points: [[x1, y1], [x2, y1], [x2, y2], [x1, y2]]
                x_coords = [p[0] for p in bbox]
                y_coords = [p[1] for p in bbox]
                x_min, x_max = min(x_coords), max(x_coords)
                y_min, y_max = min(y_coords), max(y_coords)

                blocks.append({
                    "text": text,
                    "confidence": float(confidence),
                    "bbox": [int(x_min), int(y_min), int(x_max), int(y_max)]
                })
                full_text.append(text)

        avg_conf = sum([b["confidence"] for b in blocks]) / len(blocks) if blocks else 0.0

        # Sort blocks to establish correct reading order (top-to-bottom, left-to-right)
        from services.ocr.reading_order import ReadingOrder
        sorted_blocks = ReadingOrder.sort_blocks(blocks)

        full_text = [b["text"] for b in sorted_blocks]

        duration = time.time() - start_time
        logger.info(f"OCR completed in {duration:.2f} seconds. Extracted {len(blocks)} blocks.")

        return {
            "text": "\n".join(full_text),
            "confidence": float(avg_conf),
            "blocks": sorted_blocks
        }


__all__ = ["OCREngine"]
