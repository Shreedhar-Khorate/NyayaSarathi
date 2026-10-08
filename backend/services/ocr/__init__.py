"""
NyayaSarathi Legal Document OCR Package.
Provides automated document detection, OpenCV image preprocessing, PaddleOCR integration,
reading order reconstruction, and unified legal text extraction.
"""

from .detector import DocumentDetector
from .image_preprocessor import ImagePreprocessor
from .ocr_engine import OCREngine
from .layout_analyzer import LayoutAnalyzer
from .reading_order import ReadingOrder
from .pdf_extractor import PDFExtractor
from .docx_extractor import DOCXExtractor
from .image_extractor import ImageExtractor
from .ocr_processor import LegalOCRProcessor, DocumentProcessor
from .validator import validate_file, ALLOWED_EXTENSIONS, ALLOWED_MIME_TYPES

__all__ = [
    "DocumentDetector",
    "ImagePreprocessor",
    "OCREngine",
    "LayoutAnalyzer",
    "ReadingOrder",
    "PDFExtractor",
    "DOCXExtractor",
    "ImageExtractor",
    "LegalOCRProcessor",
    "DocumentProcessor",
    "validate_file",
    "ALLOWED_EXTENSIONS",
    "ALLOWED_MIME_TYPES",
]
