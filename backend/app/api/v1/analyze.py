from fastapi import APIRouter, HTTPException
from app.schemas.analyze import CaseAnalysisRequest, CaseAnalysisResponse
from app.services.analyze_service import predict_case_outcome

router = APIRouter()

@router.post("", response_model=CaseAnalysisResponse)
def analyze_case(request: CaseAnalysisRequest):
    """Predict judgment success probability for a given case."""
    if not request.description.strip():
        raise HTTPException(status_code=400, detail="Case description cannot be empty.")
    return predict_case_outcome(request)
