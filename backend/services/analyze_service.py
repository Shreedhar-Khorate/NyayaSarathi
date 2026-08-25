"""
Judgment Success Predictor — Full ML Pipeline Service
Pipeline: Case Understanding → Retrieval → Hybrid Ranking →
          Confidence Engine → Precedent Verification →
          Grounded Explanation → Final Validation
"""
from models.prediction import (
    CaseInputRequest,
    FinalPredictionResponse,
)
from services.case_understanding import get_case_understanding_engine
from services.retrieval import get_candidate_retrieval_engine
from services.ranking import get_similarity_ranker
from services.confidence_engine import get_confidence_engine
from services.precedent_verifier import get_precedent_verifier
from services.explanation_engine import get_explanation_engine
from services.validator import get_final_validator


def predict_case_outcome(request: CaseInputRequest) -> FinalPredictionResponse:
    """Run the full NyayaSarathi prediction pipeline."""

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

    # 2. Candidate Retrieval (Local DB → DuckDuckGo fallback)
    retriever = get_candidate_retrieval_engine()
    retrieval_res = retriever.retrieve_candidates(
        profile=profile, min_candidates=15, max_candidates=50
    )

    # 3. Hybrid Similarity Ranking (Vector + BM25 RRF)
    ranker = get_similarity_ranker()
    ranked_precedents = ranker.rank_candidates(
        profile=profile,
        user_description=request.description,
        candidates=retrieval_res.candidates,
        top_k=5,
    )

    # 4. Confidence Evaluation & Abstention Guardrail
    confidence_engine = get_confidence_engine()
    conf_result = confidence_engine.generate_prediction_or_abstain(
        structured_case=profile,
        ranked_precedents=ranked_precedents,
        prior_smoothing_alpha=0.15,
    )

    # Handle Insufficient Data / Abstention
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
            limitations=[
                "Please provide more detailed case facts, cited Indian Acts "
                "(e.g. IPC, CrPC, Contract Act), or specific statutory section numbers."
            ],
            structured_case=profile,
        )

    # 5. Precedent Verification & Citation Provenance
    verifier = get_precedent_verifier()
    verified_precedents, provenance_report = verifier.verify_and_enrich(
        ranked_precedents=ranked_precedents,
        user_position=profile.user_position,
        case_type=profile.case_type,
    )

    # 6. Grounded Natural-Language Explanation
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
        legalPrecedents=[
            f"{p.case_name} ({p.court}, {p.year}) - {p.outcome}"
            for p in verified_precedents
        ],
        keyTakeaway=explanation.takeaway,
    )

    # 8. Final Anti-Hallucination Validation
    validator = get_final_validator()
    _, validation_report = validator.validate_prediction_response(
        final_response, expected_probability=prob
    )
    final_response.validation_report = validation_report

    return final_response
