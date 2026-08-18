from pydantic import BaseModel, Field
from typing import List


class CaseAnalysisRequest(BaseModel):
    case_type: str = Field(..., example="civil", description="Type of case: civil or criminal")
    description: str = Field(..., min_length=10, example="Vendor failed to deliver goods as per contract.")

class CaseAnalysisResponse(BaseModel):
    probability: str
    legal_precedents: List[str]
    key_takeaway: str
    confidence: str
