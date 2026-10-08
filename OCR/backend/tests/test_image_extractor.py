from unittest.mock import patch, MagicMock
from app.services.image_extractor import ImageExtractor

@patch('app.services.image_preprocessor.ImagePreprocessor.preprocess_image')
@patch('app.services.image_extractor.OCREngine')
def test_image_extractor(mock_ocr_engine_cls, mock_preprocess):
    mock_preprocess.return_value = MagicMock()
    
    mock_engine = MagicMock()
    mock_engine.extract.return_value = {
        "text": "Image OCR text",
        "confidence": 0.88,
        "blocks": [{"text": "Image OCR text", "confidence": 0.88, "bbox": [0,0,10,10]}]
    }
    mock_ocr_engine_cls.return_value = mock_engine
    
    extractor = ImageExtractor()
    pages = extractor.extract_text("dummy.jpg")
    
    assert len(pages) == 1
    assert pages[0]["page_number"] == 1
    assert pages[0]["text"] == "Image OCR text"
    assert pages[0]["confidence"] == 0.88
