from pydantic import BaseModel
from typing import List, Optional


class DraftRequest(BaseModel):
    draft_type: str           # e.g. "Legal Notice", "Bail Application"
    case_facts: str
    target_language: Optional[str] = None  # e.g. "hi", "mr", "ta"

class DraftResponse(BaseModel):
    draft_text: str
    translated_text: Optional[str] = None
    citations_used: List[str]
