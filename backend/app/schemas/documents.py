from pydantic import BaseModel
from typing import List


class DocumentUploadResponse(BaseModel):
    document_id: str
    page_count: int
    ocr_applied: bool
    status: str   # queued | processing | ready

class Chunk(BaseModel):
    chunk_id: str
    section_type: str   # facts | argument | ratio | order
    text: str
    page_ref: int

class ChunksResponse(BaseModel):
    document_id: str
    chunks: List[Chunk]
