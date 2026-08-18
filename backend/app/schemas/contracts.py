from pydantic import BaseModel
from typing import List


class RedFlag(BaseModel):
    clause_text: str
    risk_level: str   # low | medium | high
    explanation: str
    page_ref: int

class ContractAnalysisResponse(BaseModel):
    red_flags: List[RedFlag]
    overall_risk_score: str
