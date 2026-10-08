import os
from unittest.mock import patch, MagicMock
from app.services.pdf_extractor import PDFExtractor

@patch('app.services.pdf_extractor.fitz.open')
@patch('app.services.detector.DocumentDetector.detect_pdf_type')
def test_extract_digital_pdf(mock_detect, mock_fitz_open):
    mock_detect.return_value = {
        "pdf_type": "TEXT_PDF",
        "pages_classification": ["text"]
    }
    
    mock_doc = MagicMock()
    mock_page = MagicMock()
    mock_page.get_text.return_value = "Digital text here"
    mock_doc.__len__.return_value = 1
    mock_doc.load_page.return_value = mock_page
    mock_fitz_open.return_value = mock_doc
    
    extractor = PDFExtractor()
    pages = extractor.extract_text("dummy.pdf")
    
    assert len(pages) == 1
    assert pages[0]["page_number"] == 1
    assert pages[0]["text"] == "Digital text here"
    assert pages[0]["confidence"] is None

@patch('app.services.pdf_extractor.fitz.open')
@patch('app.services.detector.DocumentDetector.detect_pdf_type')
def test_extract_blank_pdf_page(mock_detect, mock_fitz_open):
    mock_detect.return_value = {
        "pdf_type": "TEXT_PDF",
        "pages_classification": ["blank"]
    }
    
    mock_doc = MagicMock()
    mock_page = MagicMock()
    mock_doc.__len__.return_value = 1
    mock_doc.load_page.return_value = mock_page
    mock_fitz_open.return_value = mock_doc
    
    extractor = PDFExtractor()
    pages = extractor.extract_text("dummy.pdf")
    
    assert len(pages) == 1
    assert pages[0]["text"] == "[Blank Page]"

@patch('app.services.pdf_extractor.fitz.open')
@patch('app.services.detector.DocumentDetector.detect_pdf_type')
@patch('app.services.image_preprocessor.ImagePreprocessor.preprocess_image')
@patch('app.services.pdf_extractor.OCREngine')
def test_extract_scanned_pdf(mock_ocr_engine_cls, mock_preprocess, mock_detect, mock_fitz_open):
    mock_detect.return_value = {
        "pdf_type": "SCANNED_PDF",
        "pages_classification": ["scanned"]
    }
    
    mock_doc = MagicMock()
    mock_page = MagicMock()
    mock_pix = MagicMock()
    mock_page.get_pixmap.return_value = mock_pix
    mock_doc.__len__.return_value = 1
    mock_doc.load_page.return_value = mock_page
    mock_fitz_open.return_value = mock_doc
    
    mock_preprocess.return_value = MagicMock()
    
    mock_engine = MagicMock()
    mock_engine.extract.return_value = {
        "text": "OCR text",
        "confidence": 0.95,
        "blocks": [{"text": "OCR text", "confidence": 0.95, "bbox": [0,0,10,10]}]
    }
    mock_ocr_engine_cls.return_value = mock_engine
    
    # We must patch os.path.exists and os.remove since it cleans up
    with patch('os.path.exists', return_value=True), patch('os.remove') as mock_remove:
        extractor = PDFExtractor()
        pages = extractor.extract_text("dummy.pdf")
        
    assert len(pages) == 1
    assert pages[0]["text"] == "OCR text"
    assert pages[0]["confidence"] == 0.95
    assert len(pages[0]["blocks"]) == 1
    assert mock_remove.called
