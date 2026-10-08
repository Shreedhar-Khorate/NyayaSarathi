from unittest.mock import patch, MagicMock
from app.services.detector import DocumentDetector

@patch('app.services.detector.fitz.open')
def test_detect_text_pdf(mock_fitz_open):
    mock_doc = MagicMock()
    mock_page = MagicMock()
    mock_page.get_text.return_value = "This is a long text line " * 10
    mock_doc.__len__.return_value = 1
    mock_doc.load_page.return_value = mock_page
    mock_fitz_open.return_value = mock_doc
    
    result = DocumentDetector.detect_pdf_type("dummy.pdf")
    assert result["pdf_type"] == "TEXT_PDF"
    assert result["pages_classification"] == ["text"]

@patch('app.services.detector.fitz.open')
def test_detect_scanned_pdf(mock_fitz_open):
    mock_doc = MagicMock()
    mock_page = MagicMock()
    mock_page.get_text.return_value = "Short text"
    mock_page.get_images.return_value = [("img1",)]
    mock_doc.__len__.return_value = 1
    mock_doc.load_page.return_value = mock_page
    mock_fitz_open.return_value = mock_doc
    
    result = DocumentDetector.detect_pdf_type("dummy.pdf")
    assert result["pdf_type"] == "SCANNED_PDF"
    assert result["pages_classification"] == ["scanned"]

@patch('app.services.detector.fitz.open')
def test_detect_blank_pdf(mock_fitz_open):
    mock_doc = MagicMock()
    mock_page = MagicMock()
    mock_page.get_text.return_value = ""
    mock_page.get_images.return_value = []
    mock_doc.__len__.return_value = 1
    mock_doc.load_page.return_value = mock_page
    mock_fitz_open.return_value = mock_doc
    
    result = DocumentDetector.detect_pdf_type("dummy.pdf")
    assert result["pdf_type"] == "TEXT_PDF"
    assert result["pages_classification"] == ["blank"]

@patch('app.services.detector.fitz.open')
def test_detect_mixed_pdf(mock_fitz_open):
    mock_doc = MagicMock()
    
    mock_page1 = MagicMock()
    mock_page1.get_text.return_value = "This is a long text line " * 10
    
    mock_page2 = MagicMock()
    mock_page2.get_text.return_value = "Short"
    mock_page2.get_images.return_value = [("img1",)]
    
    mock_doc.__len__.return_value = 2
    mock_doc.load_page.side_effect = [mock_page1, mock_page2]
    mock_fitz_open.return_value = mock_doc
    
    result = DocumentDetector.detect_pdf_type("dummy.pdf")
    assert result["pdf_type"] == "MIXED_PDF"
    assert result["pages_classification"] == ["text", "scanned"]
