from pydantic import BaseModel
from typing import List, Optional

class Block(BaseModel):
    text: str
    confidence: float
    bbox: List[int]

class PageData(BaseModel):
    page_number: int
    text: str
    confidence: Optional[float] = None
    blocks: Optional[List[Block]] = []

class DocumentResponse(BaseModel):
    document_id: str
    filename: str
    document_type: Optional[str] = None
    status: str
    pages: Optional[int] = None
    extraction_method: Optional[str] = None
    text: Optional[str] = None
    pages_data: Optional[List[PageData]] = []
