from unittest.mock import patch, MagicMock
from app.services.document_processor import DocumentProcessor

@patch('app.services.document_processor.DocumentDetector.detect_pdf_type')
@patch('app.services.document_processor.PDFExtractor')
def test_processor_routes_pdf(mock_pdf_extractor_cls, mock_detect):
    mock_detect.return_value = {"pdf_type": "TEXT_PDF", "pages_classification": ["text"]}
    
    mock_extractor = MagicMock()
    mock_extractor.extract_text.return_value = [{"page_number": 1, "text": "PDF text"}]
    mock_pdf_extractor_cls.return_value = mock_extractor
    
    result = DocumentProcessor.process_digital("dummy.pdf", "dummy.pdf")
    
    assert result["document_type"] == "text_pdf"
    assert result["extraction_method"] == "digital"
    assert result["text"] == "PDF text"
    assert result["pages"] == 1

@patch('app.services.document_processor.DOCXExtractor')
def test_processor_routes_docx(mock_docx_extractor):
    mock_docx_extractor.extract_text.return_value = [{"page_number": 1, "text": "DOCX text"}]
    
    result = DocumentProcessor.process_digital("dummy.docx", "dummy.docx")
    
    assert result["document_type"] == "docx"
    assert result["extraction_method"] == "digital"
    assert result["text"] == "DOCX text"

@patch('app.services.document_processor.ImageExtractor')
def test_processor_routes_image(mock_image_extractor_cls):
    mock_extractor = MagicMock()
    mock_extractor.extract_text.return_value = [{"page_number": 1, "text": "Image text"}]
    mock_image_extractor_cls.return_value = mock_extractor
    
    result = DocumentProcessor.process_digital("dummy.jpg", "dummy.jpg")
    
    assert result["document_type"] == "image"
    assert result["extraction_method"] == "paddleocr"
    assert result["text"] == "Image text"
