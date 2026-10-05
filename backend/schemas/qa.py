from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class QARequest(BaseModel):
    question: str = Field(..., min_length=2, description="Legal question to research")
    document_ids: Optional[List[str]] = Field(default=[], description="Selected document IDs to scope retrieval")
    case_id: Optional[str] = Field(default=None, description="Optional case identifier")


class Citation(BaseModel):
    source_id: str = Field(..., description="Evidence ID tag, e.g. 'S1', 'S2'")
    document_id: str
    document_title: str
    page_number: int
    paragraph_number: int
    section_title: Optional[str] = None
    excerpt: str
    chunk_id: str


class QAResponse(BaseModel):
    answer: str
    citations: List[Citation]
    insufficient_evidence: bool = False
    provider: str
    model: str


class DocumentMetadata(BaseModel):
    id: str
    title: str
    filename: str
    file_type: str
    file_size: int
    total_pages: int
    total_chunks: int
    status: str
    created_at: str
    user_id: Optional[str] = None


class DocumentListResponse(BaseModel):
    documents: List[DocumentMetadata]


class ChunkMetadata(BaseModel):
    id: str
    chunk_index: int
    page_number: int
    paragraph_number: int
    section_title: Optional[str] = None
    text: str
    token_count: int


class DocumentDetailResponse(BaseModel):
    document: DocumentMetadata
    chunks: List[ChunkMetadata]
