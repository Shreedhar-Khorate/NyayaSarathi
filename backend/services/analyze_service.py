"""
Judgment Success Predictor — Full ML Pipeline Service
Pipeline: Case Understanding → Retrieval → Hybrid Ranking →
          Confidence Engine → Precedent Verification →
          Grounded Explanation → Final Validation
"""
import time
import logging

from models.prediction import CaseInputRequest, FinalPredictionResponse
from services.case_understanding import get_case_understanding_engine
from services.retrieval import get_candidate_retrieval_engine
from services.ranking import get_similarity_ranker
from services.confidence_engine import get_confidence_engine
from services.precedent_verifier import get_precedent_verifier
from services.explanation_engine import get_explanation_engine
from services.validator import get_final_validator

log = logging.getLogger("nyayasarathi.analyze")

# ANSI shortcuts
_R = "\033[0m"
_BOLD = "\033[1m"
_DIM = "\033[2m"
_GRAY = "\033[90m"
_GREEN = "\033[92m"
_YELLOW = "\033[93m"
_RED = "\033[91m"
_CYAN = "\033[96m"
_MAGENTA = "\033[95m"
_WHITE = "\033[97m"


def _step(n: int, label: str, detail: str = "") -> None:
    detail_str = f"  {_GRAY}{detail}{_R}" if detail else ""
    log.info(
        f"{_GRAY}  Step {n}/8{_R}  {_BOLD}{_MAGENTA}{label}{_R}{detail_str}",
        extra={"component": "PIPELINE"},
    )


def predict_case_outcome(request: CaseInputRequest) -> FinalPredictionResponse:
    """Run the full NyayaSarathi prediction pipeline with structured logging."""
    t_total = time.perf_counter()

    # ── Step 1: Case Understanding & Classification ───────────────────────────
    t = time.perf_counter()
    understand_engine = get_case_understanding_engine()
    profile = understand_engine.understand_case(
        description=request.description,
        case_type=request.case_type,
        court=request.court,
        acts=request.acts,
        sections=request.sections,
        user_position=request.user_position,
    )
    ms1 = (time.perf_counter() - t) * 1000
    _step(1, "Case Understanding",
          f"type={_CYAN}{profile.case_type}{_R}{_GRAY}  "
          f"position={profile.user_position}  "
          f"sections={profile.detected_sections or '—'}  "
          f"court={profile.extracted_court or '—'}  "
          f"confidence={profile.classification_confidence:.0%}  "
          f"{ms1:.0f}ms")

    # ── Step 2: Candidate Retrieval ───────────────────────────────────────────
    t = time.perf_counter()
    retriever = get_candidate_retrieval_engine()
    retrieval_res = retriever.retrieve_candidates(
        profile=profile, min_candidates=15, max_candidates=50
    )
    ms2 = (time.perf_counter() - t) * 1000
    tiers_str = " + ".join(retrieval_res.retrieval_tiers_used) or "none"
    _step(2, "Candidate Retrieval",
          f"{_GREEN}{retrieval_res.total_candidates_found}{_R}{_GRAY} candidates  "
          f"tiers=[{tiers_str}]  {ms2:.0f}ms")

    # ── Step 3: Hybrid Similarity Ranking (Vector + BM25 + RRF) ──────────────
    t = time.perf_counter()
    ranker = get_similarity_ranker()
    ranked_precedents = ranker.rank_candidates(
        profile=profile,
        user_description=request.description,
        candidates=retrieval_res.candidates,
        top_k=5,
    )
    ms3 = (time.perf_counter() - t) * 1000
    top_sim = ranked_precedents[0].similarity if ranked_precedents else 0.0
    _step(3, "Hybrid Ranking (Vector+BM25+RRF)",
          f"{_GREEN}{len(ranked_precedents)}{_R}{_GRAY} ranked  "
          f"top_similarity={_CYAN}{top_sim:.4f}{_R}{_GRAY}  {ms3:.0f}ms")

    # ── Step 4: Confidence Evaluation & Abstention Guardrail ─────────────────
    t = time.perf_counter()
    confidence_engine = get_confidence_engine()
    conf_result = confidence_engine.generate_prediction_or_abstain(
        structured_case=profile,
        ranked_precedents=ranked_precedents,
        prior_smoothing_alpha=0.15,
    )
    ms4 = (time.perf_counter() - t) * 1000

    if conf_result.status == "insufficient_data":
        _step(4, "Confidence Engine",
              f"{_YELLOW}ABSTAINED{_R}{_GRAY}  {conf_result.message[:80]}  {ms4:.0f}ms")
        total_ms = (time.perf_counter() - t_total) * 1000
        log.info(
            f"{_YELLOW}⊘ Abstained{_R}  insufficient data  "
            f"{_GRAY}total={total_ms:.0f}ms{_R}",
            extra={"component": "PIPELINE"},
        )
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

    confidence_label = conf_result.confidence.upper()
    conf_color = _GREEN if confidence_label == "HIGH" else _YELLOW if confidence_label == "MEDIUM" else _RED
    _step(4, "Confidence Engine",
          f"probability={_CYAN}{conf_result.success_probability}%{_R}{_GRAY}  "
          f"confidence={conf_color}{confidence_label}{_R}{_GRAY}  "
          f"{ms4:.0f}ms")

    # ── Step 5: Precedent Verification & Citation Provenance ─────────────────
    t = time.perf_counter()
    verifier = get_precedent_verifier()
    verified_precedents, provenance_report = verifier.verify_and_enrich(
        ranked_precedents=ranked_precedents,
        user_position=profile.user_position,
        case_type=profile.case_type,
    )
    ms5 = (time.perf_counter() - t) * 1000
    _step(5, "Precedent Verification",
          f"{_GREEN}{len(verified_precedents)}{_R}{_GRAY} verified  "
          f"cnrs={[p.cnr[:16] for p in verified_precedents]}  {ms5:.0f}ms")

    # ── Step 6: Grounded Explanation ─────────────────────────────────────────
    t = time.perf_counter()
    explainer = get_explanation_engine()
    explanation = explainer.generate_explanation(
        structured_case=profile,
        probability=conf_result.success_probability,
        confidence=conf_result.confidence,
        precedents=verified_precedents,
    )
    ms6 = (time.perf_counter() - t) * 1000
    engine_name = explanation.synthesis_engine.split("(")[0].strip()
    _step(6, "Explanation Engine",
          f"engine={_CYAN}{engine_name}{_R}{_GRAY}  "
          f"factors={len(explanation.supporting_factors)}+ supporting  {ms6:.0f}ms")

    # ── Step 7: Map Predicted Outcome ─────────────────────────────────────────
    prob = conf_result.success_probability
    if prob >= 65:
        predicted_outcome = "favorable"
    elif prob <= 35:
        predicted_outcome = "unfavorable"
    else:
        predicted_outcome = "balanced / discretionary"

    # ── Build Final Response ──────────────────────────────────────────────────
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

    # ── Step 8: Final Anti-Hallucination Validation ───────────────────────────
    t = time.perf_counter()
    validator = get_final_validator()
    is_valid, validation_report = validator.validate_prediction_response(
        final_response, expected_probability=prob
    )
    final_response.validation_report = validation_report
    ms8 = (time.perf_counter() - t) * 1000

    valid_color = _GREEN if is_valid else _RED
    _step(8, "Validation Audit",
          f"valid={valid_color}{is_valid}{_R}{_GRAY}  "
          f"math={validation_report.math_integrity_passed}  "
          f"citations={validation_report.citation_checks_passed}  {ms8:.0f}ms")

    # ── Final Summary ─────────────────────────────────────────────────────────
    total_ms = (time.perf_counter() - t_total) * 1000
    outcome_color = _GREEN if predicted_outcome == "favorable" else _RED if predicted_outcome == "unfavorable" else _YELLOW
    log.info(
        f"{_BOLD}{_GREEN}✓ Prediction complete{_R}  "
        f"probability={_BOLD}{_CYAN}{prob}%{_R}  "
        f"confidence={_BOLD}{conf_color}{confidence_label}{_R}  "
        f"outcome={_BOLD}{outcome_color}{predicted_outcome}{_R}  "
        f"precedents={len(verified_precedents)}  "
        f"{_GRAY}total={total_ms:.0f}ms{_R}",
        extra={"component": "PIPELINE"},
    )

    return final_response
