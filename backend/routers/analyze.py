from fastapi import APIRouter, HTTPException
from schemas.analyze import CaseInputRequest, FinalPredictionResponse
from services.analyze_service import predict_case_outcome

router = APIRouter()


@router.post("", response_model=FinalPredictionResponse)
def analyze_case(request: CaseInputRequest):
    """
    Predict judgment success probability for a given Indian court case.

    Runs the full pipeline:
    Case Understanding → Retrieval (DB + DuckDuckGo) → Hybrid Ranking
    → Bayesian Confidence → Precedent Verification → Grounded Explanation
    → Anti-Hallucination Validation
    """
    if not request.description.strip():
        raise HTTPException(status_code=400, detail="Case description cannot be empty.")
    try:
        return predict_case_outcome(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")
