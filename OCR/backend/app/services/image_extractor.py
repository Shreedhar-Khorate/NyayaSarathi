import os
from typing import List, Dict, Any
from app.services.image_preprocessor import ImagePreprocessor
from app.services.ocr import OCREngine

class ImageExtractor:
    def __init__(self):
        self.ocr_engine = None
        
    def _get_ocr_engine(self):
        if self.ocr_engine is None:
            self.ocr_engine = OCREngine()
        return self.ocr_engine
        
    def extract_text(self, file_path: str) -> List[Dict[str, Any]]:
        processed_img = ImagePreprocessor.preprocess_image(file_path)
        engine = self._get_ocr_engine()
        ocr_result = engine.extract(processed_img)
        
        return [{
            "page_number": 1,
            "text": ocr_result["text"],
            "confidence": ocr_result["confidence"],
            "blocks": ocr_result["blocks"]
        }]
