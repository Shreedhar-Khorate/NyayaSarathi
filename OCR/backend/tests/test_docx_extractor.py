from unittest.mock import patch, MagicMock
from app.services.docx_extractor import DOCXExtractor

@patch('app.services.docx_extractor.docx.Document')
def test_extract_docx_paragraphs(mock_document):
    mock_doc = MagicMock()
    mock_doc.paragraphs = [MagicMock(text="Para 1"), MagicMock(text="Para 2")]
    mock_doc.tables = []
    mock_document.return_value = mock_doc
    
    pages = DOCXExtractor.extract_text("dummy.docx")
    assert len(pages) == 1
    assert pages[0]["page_number"] == 1
    assert "Para 1\nPara 2" in pages[0]["text"]

@patch('app.services.docx_extractor.docx.Document')
def test_extract_docx_tables(mock_document):
    mock_doc = MagicMock()
    mock_doc.paragraphs = []
    
    mock_table = MagicMock()
    mock_row = MagicMock()
    mock_cell = MagicMock(text="Cell 1")
    mock_row.cells = [mock_cell]
    mock_table.rows = [mock_row]
    
    mock_doc.tables = [mock_table]
    mock_document.return_value = mock_doc
    
    pages = DOCXExtractor.extract_text("dummy.docx")
    assert "Cell 1" in pages[0]["text"]

@patch('app.services.docx_extractor.docx.Document')
def test_extract_docx_empty(mock_document):
    mock_doc = MagicMock()
    mock_doc.paragraphs = []
    mock_doc.tables = []
    mock_document.return_value = mock_doc
    
    pages = DOCXExtractor.extract_text("dummy.docx")
    assert len(pages) == 1
    assert pages[0]["text"].strip() == ""
