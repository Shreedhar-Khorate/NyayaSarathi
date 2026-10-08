"""
Legal Document OCR & Extraction Schemas for NyayaSarathi.
Pydantic data models for layout blocks, page-level extractions, and unified OCR response.
"""

from pydantic import BaseModel, Field
from typing import List, Optional


class Block(BaseModel):
    """Visual or bounding-box text block with spatial coordinates."""
    text: str = Field(..., description="Extracted text snippet")
    confidence: float = Field(..., description="OCR or digital extraction confidence [0.0 - 1.0]")
    bbox: List[int] = Field(..., description="Bounding box [x_min, y_min, x_max, y_max]")
    region_type: Optional[str] = Field(None, description="Classified legal region (e.g. heading, citation, bench, paragraph)")


class PageData(BaseModel):
    """Page-level extraction data preserving natural reading order."""
    page_number: int = Field(..., description="1-indexed document page number")
    text: str = Field(..., description="Reconstructed text in reading order")
    confidence: Optional[float] = Field(None, description="Average OCR confidence for the page")
    blocks: Optional[List[Block]] = Field(default_factory=list, description="Ordered text blocks with bounding boxes")


class OCRDocumentResponse(BaseModel):
    """Unified Legal Document OCR extraction response."""
    document_id: str = Field(..., description="Unique generated document identifier")
    filename: str = Field(..., description="Original uploaded filename")
    status: str = Field("completed", description="'completed', 'processing', or 'failed'")
    document_type: Optional[str] = Field(None, description="Detected type ('text_pdf', 'scanned_pdf', 'mixed_pdf', 'docx', 'image')")
    pages: Optional[int] = Field(None, description="Total number of pages processed")
    extraction_method: Optional[str] = Field(None, description="Extraction engine ('digital', 'paddleocr', 'paddleocr_mixed')")
    text: Optional[str] = Field(None, description="Full reconstructed text across all pages")
    pages_data: Optional[List[PageData]] = Field(default_factory=list, description="Page-by-page extraction details")


# Backward compatibility alias
DocumentResponse = OCRDocumentResponse

__all__ = [
    "Block",
    "PageData",
    "OCRDocumentResponse",
    "DocumentResponse",
]
