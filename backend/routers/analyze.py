from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Header
from schemas.analyze import CaseInputRequest, FinalPredictionResponse
from services.analyze_service import predict_case_outcome
from services.auth_service import decode_access_token

router = APIRouter()


def get_optional_user_id(authorization: Optional[str] = Header(None)) -> Optional[str]:
    """Extracts user ID from Authorization header if present, else returns None."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.split(" ")[1]
    try:
        payload = decode_access_token(token)
        return payload.get("sub")
    except Exception:
        return None


@router.post("", response_model=FinalPredictionResponse)
def analyze_case(
    request: CaseInputRequest,
    user_id: Optional[str] = Depends(get_optional_user_id),
):
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
        res = predict_case_outcome(request)
        if user_id:
            try:
                from services.user_repository import create_activity
                title_preview = request.title or (request.description[:50] + "...")
                create_activity(
                    user_id=user_id,
                    activity_type="PREDICTION",
                    title=f"Prediction: {title_preview}",
                    query_text=request.description[:200],
                    metadata={
                        "verdict": getattr(res, "verdict", "N/A"),
                        "win_probability": getattr(res, "probability", None),
                    },
                )
            except Exception:
                pass
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

