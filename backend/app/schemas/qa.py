from pydantic import BaseModel
from typing import List, Optional


class QARequest(BaseModel):
    question: str
    case_id: Optional[str] = None

class Citation(BaseModel):
    document: str
    page: int
    excerpt: str

class QAResponse(BaseModel):
    answer: str
    citations: List[Citation]
