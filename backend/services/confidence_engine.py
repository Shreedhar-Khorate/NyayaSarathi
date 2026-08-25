"""
Confidence Scoring & Insufficient-Data Abstention Guardrail Engine for NyayaSarathi.

Enforces:
1. Independent, multi-factor confidence scoring (Sample Size, Similarity Density, Statutory Match, Outcome Entropy).
2. Mandatory Abstention (`status: "insufficient_data"`) when evidence is too weak, preventing hallucinated predictions.
"""

from typing import List, Optional, Tuple
import math

from models.prediction import (
    StructuredCaseProfile,
    RankedPrecedent,
    Stage3OutcomeResponse,
    ConfidenceDimensionMetrics,
    AbstentionDecision,
    ConfidencePredictionResult,
    Stage4PredictionResponse,
)
from services.outcome_engine import get_outcome_analyzer


class ConfidenceAndAbstentionEngine:
    """
    Evaluates confidence metrics and enforces abstention guardrails.
    """

    # Guardrail thresholds
    MIN_PRECEDENTS_COUNT = 2
    MIN_TOP1_SIMILARITY_THRESHOLD = 0.35
    MIN_AVG_SIMILARITY_THRESHOLD = 0.25

    def evaluate_confidence_and_abstention(
        self,
        structured_case: StructuredCaseProfile,
        ranked_precedents: List[RankedPrecedent],
    ) -> Tuple[ConfidenceDimensionMetrics, AbstentionDecision]:
        """
        Calculates multi-dimensional confidence breakdown and evaluates whether
        the system should abstain due to insufficient historical evidence.
        """
        total_p = len(ranked_precedents)

        # 1. Sample Size Metric [0.0 - 1.0]
        sample_size_score = min(1.0, round(total_p / 5.0, 4)) if total_p > 0 else 0.0

        # 2. Similarity Density Metric [0.0 - 1.0]
        if total_p == 0:
            similarity_density_score = 0.0
            top1_sim = 0.0
            avg_sim = 0.0
        else:
            top1_sim = ranked_precedents[0].similarity
            avg_sim = sum(p.similarity for p in ranked_precedents) / total_p
            # Dense similarity score combining top match strength & mean strength
            similarity_density_score = min(1.0, round((top1_sim * 0.5) + (avg_sim * 0.5), 4))

        # 3. Statutory Alignment Metric [0.0 - 1.0]
        if not structured_case.detected_sections:
            statutory_alignment_score = 0.50  # Neutral baseline when no statutory section was cited
        elif total_p == 0:
            statutory_alignment_score = 0.0
        else:
            matched_count = sum(1 for p in ranked_precedents if len(p.matched_sections) > 0)
            statutory_alignment_score = round(matched_count / total_p, 4)

        # 4. Outcome Consistency / Agreement Metric [0.0 - 1.0]
        if total_p == 0:
            outcome_consistency_score = 0.0
        else:
            outcome_analyzer = get_outcome_analyzer()
            favorable_count = 0
            unfavorable_count = 0
            neutral_count = 0

            for p in ranked_precedents:
                score, label = outcome_analyzer.map_outcome_for_position(
                    raw_disposal=p.outcome,
                    user_position=structured_case.user_position,
                    case_type=structured_case.case_type,
                )
                if score >= 0.7:
                    favorable_count += 1
                elif score <= 0.3:
                    unfavorable_count += 1
                else:
                    neutral_count += 1

            # High agreement (e.g. 5 favorable vs 0 unfavorable) -> 1.0; 50/50 split -> 0.40
            max_agreement = max(favorable_count, unfavorable_count, neutral_count)
            outcome_consistency_score = round(max_agreement / total_p, 4)

        # 5. Composite Confidence Score
        composite_score = round(
            (0.25 * sample_size_score)
            + (0.45 * similarity_density_score)
            + (0.15 * statutory_alignment_score)
            + (0.15 * outcome_consistency_score),
            4
        )

        # Categorical Rating
        if composite_score >= 0.55 and total_p >= 3 and top1_sim >= 0.42:
            rating = "high"
        elif composite_score >= 0.35 and total_p >= 2 and top1_sim >= 0.35:
            rating = "medium"
        else:
            rating = "low"

        metrics = ConfidenceDimensionMetrics(
            sample_size_score=sample_size_score,
            similarity_density_score=similarity_density_score,
            statutory_alignment_score=statutory_alignment_score,
            outcome_consistency_score=outcome_consistency_score,
            aggregate_confidence_score=composite_score,
            confidence_rating=rating,
        )

        # ── 6. Insufficient-Data Abstention Decision ─────────────────────────
        if total_p < self.MIN_PRECEDENTS_COUNT:
            return metrics, AbstentionDecision(
                should_abstain=True,
                reason_code="insufficient_sample_size",
                explanation=(
                    f"Only {total_p} historical judgment(s) were found in the database. "
                    f"At least {self.MIN_PRECEDENTS_COUNT} comparable precedents are required to produce an advisory estimate."
                ),
            )

        if structured_case.case_type == "other" and len(structured_case.detected_sections) == 0:
            return metrics, AbstentionDecision(
                should_abstain=True,
                reason_code="unrecognized_case_domain",
                explanation=(
                    "The case narrative does not match a recognized Indian legal domain and lacks cited statutory provisions or acts."
                ),
            )

        if top1_sim < self.MIN_TOP1_SIMILARITY_THRESHOLD or avg_sim < self.MIN_AVG_SIMILARITY_THRESHOLD:
            return metrics, AbstentionDecision(
                should_abstain=True,
                reason_code="low_similarity_threshold",
                explanation=(
                    f"The retrieved historical cases have low factual/statutory relevance "
                    f"(Top similarity: {round(top1_sim, 2)}, Average: {round(avg_sim, 2)} < required {self.MIN_AVG_SIMILARITY_THRESHOLD}). "
                    "NyayaSarathi refuses to generate an unfounded probability without sufficiently close precedents."
                ),
            )

        # Sufficient evidence to proceed
        return metrics, AbstentionDecision(
            should_abstain=False,
            reason_code=None,
            explanation="Sufficient comparable Indian precedents retrieved to compute a data-driven advisory probability.",
        )

    def generate_prediction_or_abstain(
        self,
        structured_case: StructuredCaseProfile,
        ranked_precedents: List[RankedPrecedent],
        prior_smoothing_alpha: float = 0.15,
    ) -> Stage4PredictionResponse:
        """
        Master decision function: returns full prediction if confident,
        or structured abstention response if evidence is insufficient.
        """
        metrics, abstention = self.evaluate_confidence_and_abstention(
            structured_case=structured_case,
            ranked_precedents=ranked_precedents,
        )

        # ── Handle Abstention ───────────────────────────────────────────────
        if abstention.should_abstain:
            return Stage4PredictionResponse(
                status="insufficient_data",
                case_type=structured_case.case_type,
                user_position=structured_case.user_position,
                success_probability=None,
                predicted_verdict=None,
                confidence="low",
                confidence_breakdown=metrics,
                abstention_info=abstention,
                precedents=[],
                precedent_valuations=[],
                outcome_distribution=None,
                probability_metrics=None,
                structured_case=structured_case,
                message=f"ABSTAINED: {abstention.explanation}",
            )

        # ── Sufficient Data: Compute Outcome Probability ────────────────────
        outcome_analyzer = get_outcome_analyzer()
        stage3_res: Stage3OutcomeResponse = outcome_analyzer.analyze_outcomes_and_predict(
            structured_case=structured_case,
            ranked_precedents=ranked_precedents,
            prior_smoothing_alpha=prior_smoothing_alpha,
            prior_baseline_prob=50.0,
        )

        return Stage4PredictionResponse(
            status="success",
            case_type=structured_case.case_type,
            user_position=structured_case.user_position,
            success_probability=stage3_res.success_probability,
            predicted_verdict=stage3_res.predicted_verdict,
            confidence=metrics.confidence_rating,
            confidence_breakdown=metrics,
            abstention_info=abstention,
            precedents=ranked_precedents,
            precedent_valuations=stage3_res.precedent_valuations,
            outcome_distribution=stage3_res.outcome_distribution,
            probability_metrics=stage3_res.probability_metrics,
            structured_case=structured_case,
            message=(
                f"Data-driven prediction computed ({stage3_res.success_probability}%) with "
                f"{metrics.confidence_rating.upper()} confidence based on {len(ranked_precedents)} historical precedents."
            ),
        )


# Singleton
_confidence_engine = None

def get_confidence_engine() -> ConfidenceAndAbstentionEngine:
    global _confidence_engine
    if _confidence_engine is None:
        _confidence_engine = ConfidenceAndAbstentionEngine()
    return _confidence_engine
