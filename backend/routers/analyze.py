"""
Master NyayaSarathi Case Analysis & Judgment Success Prediction Router.

Implements the complete data-driven prediction pipeline:
Case Understanding -> Candidate Retrieval -> Similarity Ranking ->
Confidence & Abstention Guardrails -> Real Precedent Verification ->
Grounded Explanation Layer -> Final Citation & Math Validation.
"""

from fastapi import APIRouter, HTTPException, Query, Path
from typing import Optional

from models.prediction import (
    CaseInputRequest,
    FinalPredictionResponse,
    CitationProvenanceReport,
)
from services.case_understanding import get_case_understanding_engine
from services.retrieval import get_candidate_retrieval_engine
from services.ranking import get_similarity_ranker
from services.confidence_engine import get_confidence_engine
from services.precedent_verifier import get_precedent_verifier
from services.explanation_engine import get_explanation_engine
from services.validator import get_final_validator

router = APIRouter(prefix="/api", tags=["prediction"])


@router.post("/analyze", response_model=FinalPredictionResponse)
def analyze_case(
    request: CaseInputRequest,
    top_k: int = Query(5, ge=1, le=20, description="Top precedent count"),
    prior_smoothing_alpha: float = Query(0.15, ge=0.01, le=1.0),
):
    """
    Master NyayaSarathi Judgment Success Prediction Endpoint.
    Analyzes case facts, retrieves verified Indian court precedents,
    computes Bayesian Dirichlet probability, and returns grounded explanations.
    """
    try:
        clean_top_k = int(top_k) if isinstance(top_k, (int, float)) else 5
        clean_alpha = float(prior_smoothing_alpha) if isinstance(prior_smoothing_alpha, (int, float)) else 0.15

        # 1. Case Understanding & Classification
        understand_engine = get_case_understanding_engine()
        profile = understand_engine.understand_case(
            description=request.description,
            case_type=request.case_type,
            court=request.court,
            acts=request.acts,
            sections=request.sections,
            user_position=request.user_position,
        )

        # 2. Candidate Retrieval
        retriever = get_candidate_retrieval_engine()
        retrieval_res = retriever.retrieve_candidates(
            profile=profile, min_candidates=15, max_candidates=50
        )

        # 3. Hybrid Similarity Ranking
        ranker = get_similarity_ranker()
        ranked_precedents = ranker.rank_candidates(
            profile=profile,
            user_description=request.description,
            candidates=retrieval_res.candidates,
            top_k=clean_top_k,
        )

        # 4. Confidence Evaluation & Abstention Guardrail
        confidence_engine = get_confidence_engine()
        conf_result = confidence_engine.generate_prediction_or_abstain(
            structured_case=profile,
            ranked_precedents=ranked_precedents,
            prior_smoothing_alpha=clean_alpha,
        )

        # ── Handle Insufficient Data / Abstention ───────────────────────────
        if conf_result.status == "insufficient_data":
            return FinalPredictionResponse(
                status="insufficient_data",
                success_probability=None,
                confidence="low",
                case_type=profile.case_type,
                predicted_outcome=None,
                supporting_factors=[],
                opposing_factors=[],
                precedents=[],
                takeaway=f"Insufficient comparable historical Indian court judgments found. {conf_result.message}",
                limitations=["Please provide more detailed case facts, cited Indian Acts (e.g. IPC, CrPC, Contract Act), or specific statutory section numbers."],
                structured_case=profile,
                probability=None,
                legalPrecedents=[],
                keyTakeaway=f"Insufficient data: {conf_result.message}",
            )

        # 5. Precedent Verification & Citation Provenance
        verifier = get_precedent_verifier()
        verified_precedents, provenance_report = verifier.verify_and_enrich(
            ranked_precedents=ranked_precedents,
            user_position=profile.user_position,
            case_type=profile.case_type,
        )

        # 6. Grounded Natural-Language Explanation Layer
        explainer = get_explanation_engine()
        explanation = explainer.generate_explanation(
            structured_case=profile,
            probability=conf_result.success_probability,
            confidence=conf_result.confidence,
            precedents=verified_precedents,
        )

        # 7. Map Predicted Outcome
        prob = conf_result.success_probability
        if prob >= 65:
            predicted_outcome = "favorable"
        elif prob <= 35:
            predicted_outcome = "unfavorable"
        else:
            predicted_outcome = "balanced / discretionary"

        # Build Response
        final_response = FinalPredictionResponse(
            status="success",
            success_probability=prob,
            confidence=conf_result.confidence,
            case_type=profile.case_type,
            predicted_outcome=predicted_outcome,
            supporting_factors=explanation.supporting_factors,
            opposing_factors=explanation.opposing_factors,
            precedents=verified_precedents,
            takeaway=explanation.takeaway,
            limitations=explanation.limitations,
            provenance_report=provenance_report,
            structured_case=profile,
            probability=f"{prob}%",
            legalPrecedents=[f"{p.case_name} ({p.court}, {p.year}) - {p.outcome}" for p in verified_precedents],
            keyTakeaway=explanation.takeaway,
        )

        # 8. Final Evidence & Citation Validation Guardrail
        validator = get_final_validator()
        is_valid, validation_report = validator.validate_prediction_response(
            final_response, expected_probability=prob
        )
        final_response.validation_report = validation_report

        return final_response

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Case prediction failed: {str(e)}"
        )


@router.post("/predict", response_model=FinalPredictionResponse)
def predict_case(
    request: CaseInputRequest,
    top_k: int = Query(5, ge=1, le=20),
    prior_smoothing_alpha: float = Query(0.15, ge=0.01, le=1.0),
):
    """Alias for /api/analyze."""
    return analyze_case(request, top_k=top_k, prior_smoothing_alpha=prior_smoothing_alpha)


@router.get("/precedent/{cnr}")
def get_precedent_detail(
    cnr: str = Path(..., description="Official 16-character Case Number Record (CNR)"),
):
    """
    Fetch complete judgment record, full text, and provenance metadata by CNR.
    """
    verifier = get_precedent_verifier()
    data = verifier.get_full_precedent_by_cnr(cnr)
    if not data:
        raise HTTPException(
            status_code=404, detail=f"Precedent with CNR '{cnr}' not found in local database."
        )
    return {
        "status": "success",
        "cnr": cnr,
        "judgment": data,
    }
