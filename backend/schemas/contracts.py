from pydantic import BaseModel, Field
from typing import List, Optional, Dict


class RedFlag(BaseModel):
    clause_text: str
    risk_level: str  # low | medium | high
    explanation: str
    page_ref: Optional[int] = 1
    risk_category: Optional[str] = "general"
    recommendation: Optional[str] = None
    confidence: Optional[float] = None


class ContractAnalysisResponse(BaseModel):
    filename: Optional[str] = None
    overall_risk_score: str  # "High" | "Medium" | "Low"
    summary: Optional[str] = None
    red_flags: List[RedFlag]
    risk_counts: Optional[Dict[str, int]] = Field(default_factory=dict)
    limitations: Optional[List[str]] = Field(default_factory=list)
    extraction_method: Optional[str] = None
    total_pages: Optional[int] = None

